from fastapi import APIRouter, Request, Depends, HTTPException, Query, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.database import get_session
from app.models.profile import Profile
from app.models.projects import Project
from app.models.experiences import Experience
from app.models.skills import Skill
from app.models.spoken_languages import SpokenLanguage


router = APIRouter()
_jinja_env = Environment(
    loader=FileSystemLoader('templates'),
    auto_reload=True,
    autoescape=True
)
templates = Jinja2Templates(env=_jinja_env)

SUPPORTED_LANGS = {'en', 'es', 'pt'}

def is_htmx(request: Request) -> bool:
    """Check if request is from HTMX"""
    return 'hx-request' in request.headers

def resolve_lang(lang: str) -> str:
    """Return a valid language code, defaulting to 'en'."""
    return lang if lang in SUPPORTED_LANGS else 'en'


@router.get(
    path='/',
    response_class=HTMLResponse
)
async def home(
    request: Request,
    lang: str = Query(default='en'),
    db: AsyncSession = Depends(get_session)
):
    """Landing page - loads home fragment"""
    stmt = select(Profile).limit(1)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    context = {
        'request': request, 
        'profile': profile,
        'lang': resolve_lang(lang)
    }
    
    if is_htmx(request):
        return templates.TemplateResponse('fragments/home.html', context)
        
    context['active_fragment'] = 'fragments/home.html'
    return templates.TemplateResponse('index.html', context)


@router.get(
    path='/about',
    response_class=HTMLResponse
)
async def about(
    request: Request,
    lang: str = Query(default='en'),
    db: AsyncSession = Depends(get_session)
):
    """About page"""
    stmt = select(Profile).limit(1)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    context = {
        'request': request, 
        'profile': profile,
        'lang': resolve_lang(lang)
    }
    
    if is_htmx(request):
        return templates.TemplateResponse('fragments/about.html', context)
        
    context['active_fragment'] = 'fragments/about.html'
    return templates.TemplateResponse('index.html', context)


@router.get(
    path='/projects',
    response_class=HTMLResponse
)
async def projects_list(
    request: Request,
    lang: str = Query(default='en'),
    db: AsyncSession = Depends(get_session)
):
    """Projects list page"""
    stmt = (
        select(Project)
        .options(selectinload(Project.images))
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    projects = result.scalars().all()
    
    context = {
        'request': request, 
        'projects': projects,
        'lang': resolve_lang(lang)
    }
    
    if is_htmx(request):
        return templates.TemplateResponse('fragments/projects.html', context)
        
    context['active_fragment'] = 'fragments/projects.html'
    return templates.TemplateResponse('index.html', context)


@router.get(
    path='/projects/{slug}',
    response_class=HTMLResponse
)
async def project_detail(
    slug: str,
    request: Request,
    lang: str = Query(default='en'),
    db: AsyncSession = Depends(get_session)
):
    """Single project detail - loaded in modal"""
    stmt = (
        select(Project)
        .where(Project.slug == slug)
        .options(
            selectinload(Project.images),
            selectinload(Project.skills)
        )
    )
    
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail='Project not found'
        )

    context = {
        'request': request, 
        'project': project,
        'lang': resolve_lang(lang)
    }
    
    if is_htmx(request):
        return templates.TemplateResponse('fragments/projects_expanded.html', context)
        
    context['active_fragment'] = 'fragments/project_expanded.html'
    return templates.TemplateResponse('index.html', context)


@router.get(
    path='/experience',
    response_class=HTMLResponse
)
async def experience(
    request: Request,
    lang: str = Query(default='en'),
    db: AsyncSession = Depends(get_session)
):
    """Experience timeline page"""
    stmt = select(Experience).order_by(Experience.start_date.desc())
    
    result = await db.execute(stmt)
    experiences = result.scalars().all()
    
    context = {
        'request': request, 
        'experiences': experiences,
        'today': datetime.now().date(),
        'lang': resolve_lang(lang)
    }
    
    if is_htmx(request):
        return templates.TemplateResponse('fragments/experience.html', context)
        
    context['active_fragment'] = 'fragments/experience.html'
    return templates.TemplateResponse('index.html', context)


@router.get(
    path='/skills-and-languages',
    response_class=HTMLResponse
)
async def skills_and_languages(
    request: Request,
    lang: str = Query(default='en'),
    db: AsyncSession = Depends(get_session)
):
    """Skills & languages page"""
    skills_stmt = select(Skill).order_by(Skill.name)
    langs_stmt = select(SpokenLanguage).order_by(SpokenLanguage.proficiency_level.desc())
    
    skills_result = await db.execute(skills_stmt)
    langs_result = await db.execute(langs_stmt)
    
    context = {
        'request': request,
        'skills': skills_result.scalars().all(),
        'languages': langs_result.scalars().all(),
        'lang': resolve_lang(lang)
    }
    
    if is_htmx(request):
        return templates.TemplateResponse('fragments/skills_languages.html', context)
        
    context['active_fragment'] = 'fragments/skills_languages.html'
    return templates.TemplateResponse('index.html', context)


@router.get(
    path='/contact',
    response_class=HTMLResponse
)
async def contact_form(
    request: Request,
    lang: str = Query(default='en')
):
    """Contact form page"""
    context = {
        'request': request,
        'lang': resolve_lang(lang)
    }
    
    if is_htmx(request):
        return templates.TemplateResponse('fragments/contact.html', context)
        
    context['active_fragment'] = 'fragments/contact.html'
    return templates.TemplateResponse('index.html', context)


@router.get(
    path='/chat',
    response_class=HTMLResponse
)
async def ai_chat_interface(request: Request):
    """AI chat modal interface"""
    context = {
        'request': request
    }
    
    if is_htmx(request):
        return templates.TemplateResponse('fragments/chat_modal.html', context)
        
    context['active_fragment'] = 'fragments/chat_modal.html'
    return templates.TemplateResponse('index.html', context)