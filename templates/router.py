from fastapi import APIRouter, Request, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from database.models import User, UserChat
from database.database import get_async_session
from auth.validation import get_current_active_auth_user
from pydantic import BaseModel, Field


router = APIRouter()


templates = Jinja2Templates(directory='templates')



async def get_companion_by_id(companion_id: int, session: AsyncSession) -> User:
    result = await session.execute(select(User).where(User.id == companion_id))
    companion = result.scalar_one_or_none()
    if not companion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return companion


@router.get('/', response_class=HTMLResponse)
async def get_base_page(request: Request):
    return templates.TemplateResponse('index.html', {'request': request, 'title': 'Добро пожаловать!'})


@router.get('/jwt/login/', response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request, 'title': 'Логин'})


@router.get('/register', response_class=HTMLResponse)
async def get_register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request, 'title': 'Регистрация'})


@router.get('/about_us', response_class=HTMLResponse)
async def get_about_us_page(request: Request):
    return templates.TemplateResponse('about_us.html', {'request': request, 'title': 'О нас'})


@router.get('/authenticated/', response_class=HTMLResponse)
async def get_authenticated_page(
    request: Request,
      session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_active_auth_user)):
    
    result = await session.execute(select(UserChat).where(UserChat.auth_user == current_user.id))
    chats = result.scalars().all()

    return templates.TemplateResponse('auth_index.html', {'request': request, 'title': 'Главная', 'chats': chats})


@router.get('/authenticated/search/', response_class=HTMLResponse)
async def get_search_page(request: Request, current_user: User = Depends(get_current_active_auth_user)):
    return templates.TemplateResponse('search.html', {'request': request, 'title': 'Поиск'})


@router.get("/authenticated/chat/{companion_id}", response_class=HTMLResponse)
async def get_chat_page(
    request: Request,
      companion_id: int,
        current_user: User = Depends(get_current_active_auth_user),
          session: AsyncSession = Depends(get_async_session)):
    companion = await get_companion_by_id(companion_id, session)
    
    if not companion:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return templates.TemplateResponse("chat.html", {
        "request": request,  
        "companion_id": companion_id,
        "companion_name": companion.username,
    })