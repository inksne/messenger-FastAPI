from fastapi import Depends, FastAPI, Form, APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette import status
from starlette.websockets import WebSocket, WebSocketDisconnect

from database.models import User, UserChat, Message, user_chat_association
from database.database import create_db_and_tables, get_async_session
from auth.utils import hash_password, decode_jwt_ws
from auth.auth import router as jwt_router
from auth.validation import get_current_active_auth_user, get_current_access_token_payload
from templates.router import router as base_router, generate_chat_id

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from datetime import datetime
import logging
import json


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


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# @app.websocket('/authenticated/chat/')
# async def test_chat(
#     websocket: WebSocket,
#     session: AsyncSession = Depends(get_async_session),
# ):
#     await websocket.accept()

#     token = websocket.cookies.get("access_token")
#     if not token:
#         await websocket.close(code=1008)
#         return

#     try:
#         payload = decode_jwt_ws(token)
#         current_user_name = payload.get("sub")
#         if not current_user_name:
#             raise ValueError("Invalid token payload")
#     except Exception:
#         await websocket.close(code=1008)
#         return

#     except Exception as e:
#         await websocket.send_text(f"Ошибка: Неверный токен ({str(e)}).")
#         await websocket.close(code=1008)
#         return

#     # Подключаем пользователя к менеджеру WebSocket
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()

#             # Распарсить данные из JSON
#             try:
#                 message_data = json.loads(data)
#                 message_text = message_data.get("message")
#             except json.JSONDecodeError:
#                 await websocket.send_text("Ошибка: Неверный формат данных.")
#                 continue

#             # Формируем сообщение с именем отправителя
#             formatted_message = json.dumps({
#                 "sender": current_user_name,
#                 "message": message_text
#             })

#             # Отправляем всем подключенным клиентам
#             await manager.broadcast(formatted_message)
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(json.dumps({"sender": "Система", "message": f"Пользователь {current_user_name} отключился"}))


@app.websocket("/authenticated/chat/{chat_id}/")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
    current_user: User = Depends(get_current_active_auth_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Ищем чат по ID
    result_chat = await session.execute(
        select(UserChat).where(UserChat.id == chat_id)
    )
    chat = await result_chat.scalar_one_or_none()

    if not chat:
        # Автоматически создаем чат, если его нет
        chat = UserChat(participants=[current_user])
        session.add(chat)
        await session.commit()

    # Проверяем, является ли пользователь участником чата через явное соединение таблиц
    result_participants = await session.execute(
        select(user_chat_association).where(
            user_chat_association.c.chat_id == chat_id,
            user_chat_association.c.user_id == current_user.id
        )
    )

    # Если участник не найден, закрываем соединение
    is_participant = await result_participants.scalar_one_or_none()
    if not is_participant:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"{current_user.username}: {data}")
    except WebSocketDisconnect:
        pass


#роутеры

router = APIRouter()

app.include_router(jwt_router)

app.include_router(base_router)

app.mount("/static", StaticFiles(directory="static"), name="static")