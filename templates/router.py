from fastapi import APIRouter, Request, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from database.models import User
from database.database import get_async_session
from auth.validation import get_current_active_auth_user
from pydantic import BaseModel, Field


router = APIRouter()


templates = Jinja2Templates(directory='templates')

@router.get('/')
async def get_base_page(request: Request):
    return templates.TemplateResponse('base.html', {'request': request, 'title': 'Добро пожаловать!'})


@router.get('/jwt/login/')
async def get_login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request, 'title': 'Логин'})


@router.get('/about_us')
async def get_about_us_page(request: Request):
    return templates.TemplateResponse('about_us.html', {'request': request, 'title': 'О нас'})