import tempfile
import os
import asyncio
from typing import AsyncGenerator

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine
from app.core.settings import settings
from app.core.prompts import DIGITAL_TWIN_SYSTEM_PROMPT

from app.models.rag_documents import RagDocument


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class UnsupportedLanguageError(Exception):
    """Raised when an unsupported language is requested."""
    def __init__(self, language: str, message: str):
        self.language = language
        self.message = message
        super().__init__(self.message)


# ============================================================================
# EMBEDDINGS & LLM INITIALIZATION
# ============================================================================

embeddings = OpenAIEmbeddings(
    model=settings.EMBEDDING_MODEL,
    api_key=settings.OPENAI_API_KEY
)

primary_llm = ChatGroq(
    model=settings.PRIMARY_LLM,
    api_key=settings.GROQ_API_KEY,
    temperature=0.3
)

backup_llm = ChatOpenAI(
    model=settings.BACKUP_LLM,
    api_key=settings.OPENAI_API_KEY,
    temperature=0.3
)

# High availability LLM with automatic fallback
robust_llm = primary_llm.with_fallbacks([backup_llm])


# ============================================================================
# PROMPT TEMPLATE WITH CONVERSATION HISTORY SUPPORT
# ============================================================================

prompt_template = ChatPromptTemplate.from_messages([
    ('system', DIGITAL_TWIN_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name='chat_history', optional=True),
    ('human', '{question}')
])

# The RAG chain
rag_chain = prompt_template | robust_llm | StrOutputParser()


# ============================================================================
# GREETING MESSAGES (Multi-language)
# ============================================================================

GREETING_MESSAGES = {
    'en': """Hi! I'm MatIAs, Matías Estigarribia's digital twin. 

I'm here to answer your questions about my professional experience, technical skills, projects, and background. Whether you're a recruiter, a potential client, or just curious about my work, feel free to ask me anything!

What would you like to know?""",
    
    'es': """¡Hola! Soy MatIAs, el gemelo digital de Matías Estigarribia.

Estoy aquí para responder tus preguntas sobre mi experiencia profesional, habilidades técnicas, proyectos y trayectoria. No importa si sos reclutador, cliente potencial, o simplemente un entusiasta curioso por mi trabajo, ¡preguntame lo que quieras!

¿Qué te gustaría saber?""",
    
    'pt': """Olá! Sou MatIAs, o gêmeo digital de Matías Estigarribia.

Estou aqui para responder as suas perguntas sobre minha experiência profissional, habilidades técnicas, projetos e trajetória. Seja você recrutador, cliente em potencial, ou apenas curioso sobre meu trabalho, fique à vontade para perguntar!

O que você gostaria de saber?"""
}


# ============================================================================
# LANGUAGE SUPPORT & VALIDATION
# ============================================================================

SUPPORTED_LANGUAGES = {'en', 'es', 'pt'}

UNSUPPORTED_LANGUAGE_MESSAGE = (
    "I communicate in English, Spanish, and Portuguese. "
    "Could you please rephrase your question in one of these languages?"
)

OFF_TOPIC_MESSAGES = {
    'en': "That's an interesting topic, but I'm here to discuss my professional work and experience. What would you like to know about my background or projects?",
    'es': "Es un tema interesante, pero estoy aquí para hablar sobre mi trabajo y experiencia profesional. ¿Qué te gustaría saber sobre mi trayectoria o proyectos?",
    'pt': "É um tópico interessante, mas estou aqui para discutir meu trabalho e experiência profissional. O que você gostaria de saber sobre minha trajetória ou projetos?"
}

EMBEDDING_ERROR_MESSAGES = {
    'en': "I'm having trouble processing your question right now. Could you try rephrasing it?",
    'es': "Estoy teniendo problemas para procesar tu pregunta ahora. ¿Podrías reformularla?",
    'pt': "Estou tendo problemas para processar sua pergunta agora. Poderia reformulá-la?"
}

NO_CONTEXT_MESSAGES = {
    'en': "I don't have specific information about that in my knowledge base. Please reach out through my contact form and I'll be happy to provide more details.",
    'es': "No tengo información específica sobre eso en mi base de conocimientos. Por favor contactame a través de mi formulario y estaré encantado de brindarte más detalles.",
    'pt': "Não tenho informações específicas sobre isso em minha base de conhecimento. Por favor, entre em contato através do meu formulário e terei prazer em fornecer mais detalhes."
}

LLM_ERROR_MESSAGES = {
    'en': "I apologize, but I'm experiencing technical difficulties right now. Please try again in a moment, or contact me directly through my contact form.",
    'es': "Disculpá, pero estoy experimentando dificultades técnicas en este momento. Por favor intentá nuevamente en un momento, o contactame directamente a través de mi formulario.",
    'pt': "Desculpe, mas estou enfrentando dificuldades técnicas no momento. Por favor, tente novamente em um momento, ou entre em contato diretamente através do meu formulário."
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_language(language: str) -> str:
    """
    Validates that the language is supported.
    
    Args:
        language: Language code to validate
        
    Returns:
        Validated language code (lowercase)
        
    Raises:
        UnsupportedLanguageError: If language is not supported
    """
    language = language.lower().strip()
    
    if language not in SUPPORTED_LANGUAGES:
        print(f"⚠️  Invalid language requested: {language}")
        raise UnsupportedLanguageError(
            language=language,
            message=UNSUPPORTED_LANGUAGE_MESSAGE
        )
    
    return language


def is_greeting(query: str) -> bool:
    """Detects if the user's message is a greeting."""
    greetings = [
        'hi', 'hello', 'hey', 'hola', 'ola', 'olá',
        'good morning', 'good afternoon', 'good evening',
        'buenos días', 'buenas tardes', 'buenas noches',
        'bom dia', 'boa tarde', 'boa noite' 
    ]
    query_lower = query.lower().strip()
    
    # Check if it's JUST a greeting (not "hi, what's your experience with Python?")
    return query_lower in greetings or (
        any(greeting in query_lower for greeting in greetings) and len(query.split()) <= 3
    )


def should_block_query(query: str) -> tuple[bool, str | None]:
    """
    Pre-filters obviously off-topic queries to save tokens.
    Returns (should_block, optional_reason).
    """
    hard_off_topic = [
        # English
        'weather', 'recipe for', 'cook a', 'bake a',
        'movie recommendation', 'what movie', 'what series',
        'game recommendation', 'sports score', 'who won the game',
        'write this code', 'debug this', 'fix this code', 'solve this problem for me',
        'stock price', 'bitcoin price', 'crypto price',
        'news about', 'latest news', 'current events',
        
        # Spanish (Includes unaccented versions for robust matching)
        'clima', 'pronóstico', 'pronostico', 'receta para', 'receta de', 'cocinar un', 'hornear un',
        'recomendación de película', 'recomendacion de pelicula', 'qué película', 'que pelicula', 
        'qué serie', 'que serie', 'recomendación de juego', 'recomendacion de juego', 
        'resultado del partido', 'marcador', 'quién ganó', 'quien gano',
        'escribe este código', 'escribe este codigo', 'escribime un', 'depurar esto', 
        'arregla este código', 'arregla este codigo', 'resuelve este problema', 'resolvé este',
        'precio de las acciones', 'cotización', 'cotizacion', 'precio del bitcoin', 'precio de cripto',
        'noticias sobre', 'últimas noticias', 'ultimas noticias', 'actualidad',

        # Portuguese (Includes unaccented versions for robust matching)
        'previsão do tempo', 'previsao do tempo', 'receita para', 'receita de', 'cozinhar um', 'assar um',
        'recomendação de filme', 'recomendacao de filme', 'qual filme', 'qual série', 'qual serie',
        'recomendação de jogo', 'recomendacao de jogo', 'placar', 'resultado do jogo', 'quem ganhou',
        'escreva este código', 'escreva este codigo', 'debugar isso', 'depurar isso',
        'conserte este código', 'conserta esse codigo', 'arrumar esse', 'resolva este problema',
        'preço da ação', 'preco da acao', 'cotação', 'cotacao', 'preço do bitcoin', 'preco do bitcoin',
        'notícias sobre', 'noticias sobre', 'últimas notícias', 'ultimas noticias', 'atualidades'
    ]

    query_lower = query.lower()
    
    for indicator in hard_off_topic:
        if indicator in query_lower:
            return True, "That's outside the scope of our conversation."
    
    return False, None


async def get_embedding(text: str) -> list[float]:
    """Generates an embedding vector for a given text using OpenAI."""
    return await embeddings.aembed_query(text)


# ============================================================================
# MAIN FUNCTION - DIGITAL TWIN RESPONSE
# ============================================================================

async def get_digital_twin_response(
    query: str,
    language: str,
    db: AsyncSession,
    chat_history: list[dict] | None = None
) -> str:
    """
    Generates a response as Matías's digital twin.
    
    Args:
        query: The user's question
        language: Language code ('en', 'es', 'pt')
        db: Database session
        chat_history: Optional conversation history
    
    Returns:
        The digital twin's response
        
    Raises:
        UnsupportedLanguageError: If language is not supported
    """
    
    # ========================================================================
    # STEP 0: Validate language (will raise exception if invalid)
    # ========================================================================
    validated_language = validate_language(language)
    
    
    # ========================================================================
    # STEP 1: Handle greetings
    # ========================================================================
    if is_greeting(query) and not chat_history:
        return GREETING_MESSAGES.get(validated_language, GREETING_MESSAGES['en'])
    
    
    # ========================================================================
    # STEP 2: Pre-filter off-topic queries
    # ========================================================================
    should_block, reason = should_block_query(query)
    if should_block:
        return OFF_TOPIC_MESSAGES.get(validated_language, OFF_TOPIC_MESSAGES['en'])
    
    
    # ========================================================================
    # STEP 3: Generate embedding and search for relevant context
    # ========================================================================
    try:
        query_vector = await get_embedding(query)
    except Exception as e:
        # Fallback if embedding fails
        print(f"❌ Embedding error: {e}")
        return EMBEDDING_ERROR_MESSAGES.get(validated_language, EMBEDDING_ERROR_MESSAGES['en'])
    
    # Search ONLY for documents in the validated language (STRICT filter)
    stmt = (
        select(RagDocument)
        .where(RagDocument.language == validated_language)
        .where(RagDocument.active == True)
        .order_by(RagDocument.embedding.cosine_distance(query_vector))
        .limit(5)
    )
    
    result = await db.execute(stmt)
    docs = result.scalars().all()
    
    # Build context from retrieved documents
    if not docs:
        # No context found - cannot answer (ZERO HALLUCINATION)
        return NO_CONTEXT_MESSAGES.get(validated_language, NO_CONTEXT_MESSAGES['en'])
    
    context_text = '\n\n---\n\n'.join([doc.content for doc in docs])
    
    
    # ========================================================================
    # STEP 4: Convert chat history to LangChain message format
    # ========================================================================
    history_messages = []
    if chat_history:
        for msg in chat_history:
            if msg['role'] == 'user':
                history_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                history_messages.append(AIMessage(content=msg['content']))
    
    
    # ========================================================================
    # STEP 5: Generate response using RAG chain
    # ========================================================================
    try:
        response = await rag_chain.ainvoke({
            'context': context_text,
            'question': query,
            'chat_history': history_messages if history_messages else []
        })
        return response
    
    except Exception as e:
        # Graceful error handling
        print(f"❌ LLM error: {e}")
        return LLM_ERROR_MESSAGES.get(validated_language, LLM_ERROR_MESSAGES['en'])


# ============================================================================
# STREAMING FUNCTION - DIGITAL TWIN RESPONSE (SSE)
# ============================================================================

async def stream_digital_twin_response(
    query: str,
    language: str,
    db: AsyncSession,
    chat_history: list[dict] | None = None
) -> AsyncGenerator[str, None]:
    """
    Streams the digital twin response token-by-token using Server-Sent Events.

    Mirrors get_digital_twin_response but uses .astream() on the RAG chain.
    Short-circuit paths (greeting, off-topic, no context, errors) yield
    their full message as a single chunk.

    After streaming completes, the full reply is persisted to the database.

    Args:
        query: The user's question
        language: Language code ('en', 'es', 'pt')
        db: Database session
        chat_history: Optional conversation history

    Yields:
        str chunks of the AI reply

    Raises:
        UnsupportedLanguageError: If language is not supported
    """

    # ========================================================================
    # STEP 0: Validate language
    # ========================================================================
    validated_language = validate_language(language)  # raises UnsupportedLanguageError if invalid

    # ========================================================================
    # STEP 1: Handle greetings (short-circuit)
    # ========================================================================
    if is_greeting(query) and not chat_history:
        greeting = GREETING_MESSAGES.get(validated_language, GREETING_MESSAGES['en'])
        yield greeting
        return

    # ========================================================================
    # STEP 2: Pre-filter off-topic queries (short-circuit)
    # ========================================================================
    should_block, _ = should_block_query(query)
    if should_block:
        yield OFF_TOPIC_MESSAGES.get(validated_language, OFF_TOPIC_MESSAGES['en'])
        return

    # ========================================================================
    # STEP 3: Generate embedding and search for relevant context
    # ========================================================================
    try:
        query_vector = await get_embedding(query)
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        yield EMBEDDING_ERROR_MESSAGES.get(validated_language, EMBEDDING_ERROR_MESSAGES['en'])
        return

    stmt = (
        select(RagDocument)
        .where(RagDocument.language == validated_language)
        .where(RagDocument.active == True)
        .order_by(RagDocument.embedding.cosine_distance(query_vector))
        .limit(5)
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()

    if not docs:
        yield NO_CONTEXT_MESSAGES.get(validated_language, NO_CONTEXT_MESSAGES['en'])
        return

    context_text = '\n\n---\n\n'.join([doc.content for doc in docs])

    # ========================================================================
    # STEP 4: Convert chat history to LangChain message format
    # ========================================================================
    history_messages = []
    if chat_history:
        for msg in chat_history:
            if msg['role'] == 'user':
                history_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                history_messages.append(AIMessage(content=msg['content']))

    # ========================================================================
    # STEP 5: Stream response using RAG chain (.astream)
    # ========================================================================
    full_reply = ""
    try:
        async for chunk in rag_chain.astream({
            'context': context_text,
            'question': query,
            'chat_history': history_messages if history_messages else []
        }):
            full_reply += chunk
            yield chunk

    except Exception as e:
        print(f"❌ LLM streaming error: {e}")
        error_msg = LLM_ERROR_MESSAGES.get(validated_language, LLM_ERROR_MESSAGES['en'])
        yield error_msg
        return

    # ========================================================================
    # STEP 6: Persist the full conversation to DB (after stream completes)
    # ========================================================================
    if full_reply:
        try:
            from app.models.chat_logs import ChatLog
            chat_log = ChatLog(
                user_message=query,
                bot_reply=full_reply,
                language=validated_language
            )
            db.add(chat_log)
            await db.commit()
        except Exception as db_error:
            print(f"⚠️  Failed to save streaming chat log: {db_error}")
            await db.rollback()


# ============================================================================
# OPTIONAL: Get initial greeting for new conversations
# ============================================================================

def get_initial_greeting(language: str = 'en') -> str:
    """
    Returns the initial greeting message for a new conversation.
    
    Raises:
        UnsupportedLanguageError: If language is not supported
    """
    validated_language = validate_language(language)  # Will raise if invalid
    return GREETING_MESSAGES.get(validated_language, GREETING_MESSAGES['en'])


# ============================================================================
# DOCUMENT PROCESSING & EMBEDDING (Background Task)
# ============================================================================

async def process_and_embed_document(file_bytes: bytes, filename: str, language: str):
    """
    Processes a document (PDF, MD, TXT) and stores its embeddings in the database.
    Serverless-safe: Uses a temporary file that is immediately cleaned up.
    """
    print(f"🧠 Starting background processing for {filename}...")
    
    # Validate language before processing
    try:
        validated_language = validate_language(language)
    except UnsupportedLanguageError:
        print(f"⚠️  Invalid language '{language}' for document. Defaulting to 'en'")
        validated_language = 'en'
    
    ext = os.path.splitext(filename)[1].lower()
    
    # 2. NEW: Create a secure, temporary file just for LangChain to read
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        temp_file.write(file_bytes)
        temp_filepath = temp_file.name

    try:
        # Select appropriate loader based on file type using the TEMP file path
        if ext == ".pdf":
            loader = PyPDFLoader(temp_filepath)
        elif ext in [".md", ".txt"]:
            loader = TextLoader(temp_filepath, encoding="utf-8")
        else:
            print(f"❌ Unsupported file type: {ext}")
            return

        # Push the heavy synchronous file reading to a background thread
        docs = await asyncio.to_thread(loader.load)
        
        # Configure text splitter for optimal chunk size
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, 
            chunk_overlap=100
        )
        
        # Push the heavy text splitting to a background thread as well
        chunks = await asyncio.to_thread(text_splitter.split_documents, docs)
        
        # Connect to the database and save the vectors
        async with AsyncSession(engine) as session:
            for chunk in chunks:
                vector = await embeddings.aembed_query(chunk.page_content)
                
                new_doc = RagDocument(
                    source=filename, # Save the real filename, not the ugly temp name!
                    content=chunk.page_content,
                    language=validated_language,
                    embedding=vector,
                    active=True
                )
                session.add(new_doc)
                
            await session.commit()
            print(f"✅ Background processing complete! {len(chunks)} vectors added to Neon for language '{validated_language}'.")
            
    finally:
        # 3. CRITICAL: Always delete the temp file, even if the AI crashes!
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
