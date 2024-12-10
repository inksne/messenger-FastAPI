from fastapi import APIRouter, Request, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette import status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import String, cast

from database.models import User, UserChat, Message
from database.database import get_async_session
from auth.validation import get_current_active_auth_user
from auth.utils import decode_jwt_ws

from typing import List
from pydantic import BaseModel
import logging

logger = logging.Logger(__name__)


router = APIRouter()


templates = Jinja2Templates(directory='templates')


class ChatRequest(BaseModel):
    companion_username: str


def generate_chat_id(user1_id: int, user2_id: int) -> str:
    return f"chat_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"


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


@router.post('/create_chat/')
async def create_chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    
    companion_username = request.companion_username

    companion_user = (
        await session.execute(select(User).where(User.username == companion_username))
    ).scalar_one_or_none()
    
    if not companion_user:
        return templates.TemplateResponse('404.html', {'request': request, 'title': 'Пользователь не найден'})
    
    existing_chat = (
        await session.execute(
            select(UserChat).where(
                cast(UserChat.participants['auth_user'], String).in_([current_user.username, companion_username]),
                cast(UserChat.participants['companion_user'], String).in_([current_user.username, companion_username])
            )
        )
    ).scalar_one_or_none()

    if existing_chat:
        return {"message": "Чат уже существует", "chat_id": existing_chat.id}

    new_chat = UserChat(
        participants={
            "auth_user": current_user.username,
            "companion": companion_username
        }
    )
    session.add(new_chat)
    await session.commit()
    await session.refresh(new_chat)

    return {"message": "Chat created", "chat_id": new_chat.id}


@router.get('/authenticated/', response_class=HTMLResponse)
async def get_authenticated_page(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    all_chats = (
        await session.execute(select(UserChat))
    ).scalars().all()


    result_chat = [
        chat for chat in all_chats
        if chat.participants.get("auth_user") == current_user.username
    ]


    if not result_chat:
        result_chat = [
            chat for chat in all_chats
            if chat.participants.get("companion") == current_user.username
        ]

    chats_with_companion = []
    for chat in result_chat:
        companion_username = (
            chat.participants["companion"]
            if chat.participants["auth_user"] == current_user.username
            else chat.participants["auth_user"]
        )

        companion_user = (
            await session.execute(select(User).where(User.username == companion_username))
        ).scalar_one_or_none()

        companion_name = companion_user.username if companion_user else "Аноним"
        chats_with_companion.append({'chat': chat, 'companion_name': companion_name})

    return templates.TemplateResponse('auth_index.html', {
        'request': request,
        'title': 'Главная',
        'chats_with_companion': chats_with_companion,
        'current_user': current_user,
    })




@router.get('/authenticated/search/', response_class=HTMLResponse)
async def get_search_page(
    request: Request,
    query: str = '',
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user),
):
    users = []
    if query:  
        result = await session.execute(select(User).where(User.username.ilike(f"%{query}%")))
        users = result.scalars().all()
    
    return templates.TemplateResponse('search.html', {
        'request': request,
        'title': 'Поиск',
        'current_user': current_user,
        'users': users,  
        'query': query,
    })


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения: {e}")


manager = ConnectionManager()


async def verify_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    try:
        payload = decode_jwt_ws(access_token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Некорректный токен")
        return username
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Ошибка токена: {e}")


@router.get('/authenticated/chat/{chat_id}', response_class=HTMLResponse)
async def get_chat_page(
    chat_id: int,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    chat = await session.execute(select(UserChat).where(UserChat.id == chat_id))
    chat = chat.scalar_one_or_none()

    if not chat:
        return templates.TemplateResponse('404.html', {'request': request, 'title': 'Пользователь не найден'})

    participants = chat.participants
    if current_user.username not in [participants["auth_user"], participants["companion"]]:
        return templates.TemplateResponse('403.html', {'request': request, 'title': 'Недостаточно прав'})

    companion_username = (
        participants["companion"] if participants["auth_user"] == current_user.username else participants["auth_user"]
    )

    return templates.TemplateResponse('chat.html', {
        'request': request,
        'title': f'Чат с {companion_username}',
        'chat_id': chat_id,
        'companion_username': companion_username,
        'current_user': current_user,
    })


@router.websocket("/authenticated/chat/")
async def chat_websocket(
    websocket: WebSocket,
    access_token: str = Cookie(None),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        user = await verify_user(access_token)
        await manager.connect(websocket)
        await manager.broadcast(f"{user} зашел в чат.")

        while True:
            data = await websocket.receive_json()

            if data.get("action") == "load_history":
                chat_id = data.get("chat_id")
                if not chat_id:
                    await websocket.send_text("Ошибка: chat_id не указан.")
                    continue

                messages = await session.execute(
                    select(Message)
                    .where(Message.chat_id == int(chat_id))
                    .order_by(Message.sended_at.asc())
                )
                messages = messages.scalars().all()

                for msg in messages:
                    await websocket.send_text(f"{msg.author_username}: {msg.content}")

            elif data.get("action") == "send_message":
                message_content = data.get("content")
                chat_id = data.get("chat_id")

                if not message_content or not chat_id:
                    await websocket.send_text("Ошибка: Сообщение или chat_id не указаны.")
                    continue

                await manager.broadcast(f"{user}: {message_content}")

                new_message = Message(content=message_content, author_username=user, chat_id=int(chat_id))
                session.add(new_message)
                await session.commit()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{user} вышел из чата.")
    except HTTPException as e:
        await websocket.close(code=1008)