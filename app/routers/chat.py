from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.chat_logs import ChatLog
from app.schemas.chat import ChatRequestSchema, ChatResponseSchema
from app.services.ai_service import (
    get_digital_twin_response,
    stream_digital_twin_response,
    UnsupportedLanguageError,
)
from app.core.rate_limit import limiter


router = APIRouter()


@router.post(
    path='/',
    status_code=status.HTTP_200_OK,
    response_model=ChatResponseSchema,
    summary='Ask my MatIAs (my digital twin) a question'
)
@limiter.limit('10/minute')
async def ask_digital_twin(
    request: Request,
    payload: ChatRequestSchema,
    db: AsyncSession = Depends(get_session)
):
    """
    Main chat endpoint for MatIAs digital twin.

    Handles:
    - Language validation (only en, es, pt supported)
    - Digital twin response generation
    - Conversation logging (with graceful failure)

    Returns the bot's response even if logging fails.
    """

    try:
        # Get response from digital twin (will raise UnsupportedLanguageError if invalid)
        actual_reply = await get_digital_twin_response(
            query=payload.message,
            language=payload.language,
            db=db
        )

        # Try to log the conversation (but don't fail if this breaks)
        try:
            chat_log = ChatLog(
                user_message=payload.message,
                bot_reply=actual_reply,
                language=payload.language
            )
            db.add(chat_log)
            await db.commit()

        except Exception as db_error:
            # Log the database error but don't fail the request
            print(f"⚠️  Failed to save chat log to database: {db_error}")
            # Rollback to prevent hanging transactions
            await db.rollback()
            # Continue - user still gets their response

        return ChatResponseSchema(reply=actual_reply)

    except UnsupportedLanguageError as e:
        # Handle unsupported language gracefully - return 400 Bad Request
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "unsupported_language",
                "message": e.message,
                "requested_language": e.language,
                "supported_languages": ["en", "es", "pt"]
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 400, 404, etc.)
        raise

    except Exception as e:
        # Log unexpected errors for debugging
        print(f"❌ Unexpected error in chat endpoint: {e}")

        # Return generic error message (don't expose internal details)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "I'm experiencing technical difficulties right now. Please try again in a moment."
            }
        )


@router.post(
    path='/stream/',
    summary='Stream a response from MatIAs (SSE)',
)
@limiter.limit('10/minute')
async def stream_digital_twin(
    request: Request,
    payload: ChatRequestSchema,
    db: AsyncSession = Depends(get_session)
):
    """
    Streaming chat endpoint for MatIAs digital twin.

    Returns a text/event-stream response where each SSE frame carries one
    text chunk from the LLM.  The stream ends with `data: [DONE]`.

    Client-side: consume with the native Fetch API + ReadableStream.
    Do NOT use HTMX for this endpoint — HTMX does not support streaming.
    """

    async def sse_generator():
        try:
            async for chunk in stream_digital_twin_response(
                query=payload.message,
                language=payload.language,
                db=db,
                chat_history=payload.chat_history,
            ):
                # Escape newlines so each SSE frame stays on one logical line
                safe_chunk = chunk.replace('\n', '\\n')
                yield f"data: {safe_chunk}\n\n"

        except UnsupportedLanguageError as e:
            yield f"data: [ERROR] {e.message}\n\n"

        except Exception as e:
            print(f"❌ Unexpected streaming error: {e}")
            yield "data: [ERROR] I'm experiencing technical difficulties. Please try again.\n\n"

        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable Nginx buffering if proxied
        },
    )
