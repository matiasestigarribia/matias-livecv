from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sqladmin import Admin

from app.admin.auth import authentication_backend
from app.admin.views import (
    ContactMessageAdmin,
    ExperienceAdmin,
    ProfileAdmin,
    ProjectAdmin,
    ProjectImageAdmin,
    SkillAdmin,
    SpokenLanguageAdmin,
    UserAdmin,
    RagDocumentAdmin,
    ChatLogAdmin,
    UploadedDocumentAdmin,
)

from app.core.database import engine, get_session
from app.core.rate_limit import limiter
from app.routers import (
    contact_messages,
    experiences,
    profile,
    projects,
    skills,
    spoken_languages,
    chat,
    pages
)

app = FastAPI(
    title="Live CV & Digital Twin API",
    description="The backend engine for Matias Estigarribia's interactive portfolio.",
    version="1.0.0"
)

app.mount('/static', StaticFiles(directory='static'), name='static')
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

templates = Jinja2Templates(directory='templates')

app.include_router(
    router=profile.router,
    prefix='/api/v1/profile',
    tags=['Profile'],
)

app.include_router(
    router=contact_messages.router,
    prefix='/api/v1/contactmessage',
    tags=['Contact message'],
)

app.include_router(
    router=experiences.router,
    prefix='/api/v1/experiences',
    tags=['Experiences'],
)

app.include_router(
    router=projects.router,
    prefix='/api/v1/projects',
    tags=['Projects'],
)

app.include_router(
    router=skills.router,
    prefix='/api/v1/skills',
    tags=['Skills'],
)

app.include_router(
    router=spoken_languages.router,
    prefix='/api/v1/spoken_languages',
    tags=['Spoken languages'],
)

app.include_router(
    router=chat.router,
    prefix='/api/v1/chat',
    tags=['Chat with MatIAs']
)

app.include_router(
    router=pages.router,
    tags=['Frontend routes']
)

admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    title='Live Cv Admin Panel'
)

admin.add_view(UserAdmin)
admin.add_view(ProfileAdmin)
admin.add_view(ExperienceAdmin)
admin.add_view(SpokenLanguageAdmin)
admin.add_view(ContactMessageAdmin)
admin.add_view(SkillAdmin)
admin.add_view(ProjectAdmin)
admin.add_view(ProjectImageAdmin)
admin.add_view(ChatLogAdmin)
admin.add_view(RagDocumentAdmin)
admin.add_view(UploadedDocumentAdmin)


@app.get('/health')
async def health_check(db: AsyncSession = Depends(get_session)):
    """
    Hit every 4-5 mins by an external Cron job to prevent
    Cold Starts on both Cloud Run (Server) and Neon (Database).
    """
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "online",
            "database": "connected",
            "message": "System nominal. Server and Database are warm."
        }
    except Exception as e:
        return {
            "status": "degraded",
            "database": "disconnected",
            "detail": str(e)
        }
