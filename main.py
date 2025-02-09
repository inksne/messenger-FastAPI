from fastapi import Depends, FastAPI, Form, APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from contextlib import asynccontextmanager

from database.models import User
from database.database import create_db_and_tables, get_async_session
from auth.utils import hash_password
from auth.auth import router as jwt_router
from templates.router import router as base_router

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from typing import Optional
from pydantic import BaseModel
from datetime import datetime


app = FastAPI(title='messenger')


#CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

#pydantic модели для RESTfulAPI

class UserResponse(BaseModel):
    id: int
    email: Optional[str] = None
    username: str
    registered_at: datetime


#бд

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)


@app.post('/register', response_model=UserResponse)
async def register(
    username: str = Form(...),
    password: str = Form(...),
    email: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_async_session)
):
    if email in [None, '', 'null']:
        email = None
    hashed_password = hash_password(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password, email=email)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@app.post('/authenticated/search/{companion_name}')
async def search(companion_name: str, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).where(User.username.ilike(f"%{companion_name}%")))
    companions = result.scalars().all()

    if not companions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Не найдено пользователей с похожим именем.')
    
    return companions


#роутеры

router = APIRouter()

app.include_router(jwt_router)

app.include_router(base_router)

app.mount("/static", StaticFiles(directory="static"), name="static")