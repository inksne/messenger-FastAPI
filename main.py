from fastapi import Depends, FastAPI, Form, APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.websockets import WebSocket

from database.models import User, UserChat, Message
from database.database import create_db_and_tables, get_async_session
from auth.utils import hash_password
from auth.auth import router as jwt_router
from auth.validation import get_current_active_auth_user
from templates.router import router as base_router

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import logging
from datetime import datetime


logger = logging.Logger(__name__)


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
@app.on_event("startup")
async def startup():
    await create_db_and_tables()


@app.get('/authenticated/search/all_users')
async def get_all_users(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User))
    users = result.scalars().all()

    return users


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


# вебсокеты

@app.websocket('/authenticated/chat/{companion_id}')
async def chat(
    websocket: WebSocket,
      companion_id: int,
        session: AsyncSession = Depends(get_async_session),
          current_user: User = Depends(get_current_active_auth_user),
):
    await websocket.accept()
    
    result_companion = await session.execute(select(User).where(User.id == companion_id))
    companion = result_companion.scalar_one_or_none()

    if not companion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден.')
    
    result_chat = await session.execute(
        select(UserChat).filter((
            UserChat.auth_user == current_user.id) & (UserChat.companion == companion_id)))
    chat = result_chat.scalar_one_or_none()

    if not chat:
        chat = UserChat(auth_user=current_user.id, companion=companion_id, last_message_time=datetime.utcnow())

    session.add(chat)
    await session.commit()
    await session.refresh(chat)

    while True:
        message_text = await websocket.receive_text()

        new_message = Message(sender_id=current_user.id, receiver_id=companion_id, content=message_text)
        session.add(new_message)
        await session.commit()
        await session.refresh(new_message)

        chat.last_message_id = new_message.id
        chat.last_message_time = datetime.utcnow()
        await session.commit()

        await websocket.send_text(message_text)


#роутеры

router = APIRouter()

app.include_router(jwt_router)

app.include_router(base_router)

app.mount("/static", StaticFiles(directory="static"), name="static")