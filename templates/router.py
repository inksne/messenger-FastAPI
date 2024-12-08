from fastapi import APIRouter, Request, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, Cookie, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import any_
from database.models import User, UserChat
from database.database import get_async_session
from auth.validation import get_current_active_auth_user
from auth.utils import decode_jwt_ws
from typing import List

import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()


templates = Jinja2Templates(directory='templates')


def generate_chat_id(user1_id: int, user2_id: int) -> str:
    """Генерация уникального chat_id для пары пользователей."""
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


@router.get('/authenticated/', response_class=HTMLResponse)
async def get_authenticated_page(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    result_chat = (
        await session.execute(
            select(UserChat)
            .where(current_user.username == any_(UserChat.participants))
        )
    ).scalars().all()
    print(result_chat)
    chats = result_chat

    chat_with_companion = []
    for chat in chats:
        companion_id = chat.companion if chat.auth_user == current_user.id else chat.auth_user
        companion = await session.execute(select(User).where(User.id == companion_id))
        companion_user = companion.scalar_one_or_none()
        companion_name = companion_user.username if companion_user else 'Аноним'
        chat_with_companion.append({'chat': chat, 'companion_name': companion_name})

    return templates.TemplateResponse('auth_index.html', {
        'request': request,
        'title': 'Главная',
        'chats_with_companion': chat_with_companion,
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
        logger.info(f"Новое подключение. Всего подключений: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Отключение. Всего подключений: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        logger.info(f"Отправка сообщения всем ({len(self.active_connections)}) клиентам: {message}")
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


# @router.get('/authenticated/chat/', response_class=HTMLResponse)
# async def get_chat_page(request: Request):
#     return templates.TemplateResponse('chat.html', {'request': request, 'title': 'Чат'})


# @router.websocket("/authenticated/chat/")
# async def chat_websocket(websocket: WebSocket, access_token: str = Cookie(None)):
#     try:
#         user = await verify_user(access_token)
#         await manager.connect(websocket)
#         await manager.broadcast(f"Пользователь {user} присоединился к чату.")
        
#         while True:
#             data = await websocket.receive_text()
#             await manager.broadcast(f"{user}: {data}")
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"Пользователь {user} покинул чат.")
#     except HTTPException as e:
#         await websocket.close(code=1008)


@router.get("/authenticated/create_chat/", response_class=HTMLResponse)
async def create_chat_page(request: Request):
    # Отображение формы для создания чата
    return templates.TemplateResponse(
        "create_chat.html", {"request": request, "title": "Создание чата"}
    )


@router.post("/authenticated/create_chat/")
async def create_chat(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user),
    participants: str = Form(...),  
):
    # Преобразуем строку участников в список
    participant_ids = [int(pid.strip()) for pid in participants.split(",")]

    # Проверяем, существуют ли все указанные пользователи
    users = await session.execute(select(User).where(User.id.in_(participant_ids)))
    users = users.scalars().all()

    if len(users) != len(participant_ids):
        raise HTTPException(status_code=400, detail="Некоторые пользователи не найдены")

    # Создаем чат и добавляем текущего пользователя
    chat = UserChat(participants=users)
    chat.participants.append(current_user)
    session.add(chat)
    await session.commit()

    return templates.TemplateResponse(
        "chat_created.html",
        {"request": request, "title": "Чат создан", "chat_id": chat.id},
    )


@router.get("/authenticated/chat/{chat_id}/", response_class=HTMLResponse)
async def chat_page(request: Request, chat_id: int, session: AsyncSession = Depends(get_async_session)):
    # Проверка, существует ли чат
    chat_exists = await session.execute(
        select(UserChat).where(UserChat.id == chat_id)
    )
    if not chat_exists.scalar_one_or_none():
        return HTMLResponse(content="Чат не найден", status_code=404)

    # Рендеринг шаблона
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "title": "Чат", "chat_id": chat_id},
    )