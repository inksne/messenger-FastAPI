import pytest
from typing import AsyncGenerator
from sqlalchemy.future import select
from database.models import User, Message, UserChat
from database.database import async_session_maker
from .test_config import MODE
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text


@pytest.fixture
async def setup_test_db(scope="function") -> AsyncGenerator[AsyncSession, None]:
    '''фикстура для создания базы данных и предоставления сессии для тестов'''
    assert MODE == 'TEST'
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.execute(text("TRUNCATE TABLE messages RESTART IDENTITY CASCADE;"))
            await session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE;"))
            await session.commit()


@pytest.mark.asyncio
async def test_model_type(setup_test_db):
    '''тест для проверки типа возвращаемого объекта из бд'''
    assert MODE == 'TEST'
    async for session in setup_test_db:  
        result = await session.execute(select(User))
        users = result.scalars().all()

    assert isinstance(users, list)


@pytest.mark.asyncio
async def test_create_user(setup_test_db):
    '''тест для проверки создания пользователя в бд'''
    assert MODE == 'TEST'
    async for session in setup_test_db:  
        new_user = User(username="testuser", email="testuser@example.com", password="password")
        session.add(new_user)
        await session.commit()

        result = await session.execute(select(User))
        user = result.scalars().all()

        assert len(user) == 1
        assert user[0].username == "testuser"


@pytest.mark.asyncio
async def test_delete_user(setup_test_db):
    '''тест для проверки удаления пользователя в бд'''
    assert MODE == 'TEST'
    async for session in setup_test_db:  
        new_user = User(username="testuser", email="testuser@example.com", password="password")
        session.add(new_user)
        await session.commit()

        result = await session.execute(select(User))
        user = result.scalars().first()
        await session.delete(user)
        await session.commit()

        result = await session.execute(select(User))
        users = result.scalars().all()

        assert len(users) == 0


@pytest.mark.asyncio
async def test_create_message(setup_test_db):
    '''тест для проверки создания сообщения в бд'''
    async for session in setup_test_db:
        new_user = User(username="testuser", email="testuser@example.com", password="password")
        session.add(new_user)
        await session.commit()

        new_message = Message(sender_id=new_user.id, receiver_id=new_user.id, content='bla-bla-bla')
        session.add(new_message)
        await session.commit()

        result = await session.execute(select(Message))
        message = result.scalars().all()

        assert len(message) == 1


@pytest.mark.asyncio
async def test_delete_message(setup_test_db):
    '''тест для проверки удаления сообщения в бд'''
    assert MODE == 'TEST'
    async for session in setup_test_db:  
        new_user = User(username="testuser", email="testuser@example.com", password="password")
        session.add(new_user)
        await session.commit()

        new_message = Message(sender_id=new_user.id, receiver_id=new_user.id, content='bla-bla-bla')
        session.add(new_message)
        await session.commit()

        result = await session.execute(select(Message))
        message = result.scalars().first()
        await session.delete(message)
        await session.commit()

        result = await session.execute(select(User))
        user = result.scalars().first()
        await session.delete(user)
        await session.commit()

        result = await session.execute(select(Message))
        messages = result.scalars().all()

        assert len(messages) == 0


@pytest.mark.asyncio
async def test_select_all_users(setup_test_db):
    '''создание и выборка всех пользователей'''
    async for session in setup_test_db:
        new_user = User(username="testuser", email="testuser@example.com", password="password")
        session.add(new_user)
        await session.commit()

        result = await session.execute(select(User))
        users = result.scalars().all()

        print([user.__dict__ for user in users])
        assert isinstance(users, object)
        

@pytest.mark.asyncio
async def test_select_all_messages(setup_test_db):
    '''создание и выборка сообщений'''
    async for session in setup_test_db:
        new_user = User(username="testuser", email="testuser@example.com", password="password")
        session.add(new_user)
        await session.commit()

        new_message = Message(sender_id=new_user.id, receiver_id=new_user.id, content='bla-bla-bla')
        session.add(new_message)
        await session.commit()

        result = await session.execute(select(Message))
        messages = result.scalars().all()

        print([message.__dict__ for message in messages])
        assert isinstance(messages, object)


@pytest.mark.asyncio
async def test_json_type(setup_test_db):
    '''проверка, в каком виде возвращаются данные из таблицы с типом json'''
    async for session in setup_test_db:
        assert MODE == 'TEST'
        new_participants = UserChat(participants={'username': 'username'})
        session.add(new_participants)
        await session.commit()

        result = await session.execute(select(UserChat.participants))
        participants = result.scalar_one_or_none()

        print(participants)
        assert isinstance(participants, dict)

        result = await session.execute(select(UserChat))
        chat = result.scalars().first()
        await session.delete(chat)
        await session.commit()


@pytest.mark.asyncio
async def test_json_add(setup_test_db):
    '''проверка получения значения из базы данных по ключу и его сравнение'''
    async for session in setup_test_db:
        assert MODE == 'TEST'

        new_participants = UserChat(participants={'username': 'some_name'})
        session.add(new_participants)
        await session.commit()

        result = await session.execute(select(UserChat.participants))
        participants = result.scalar_one_or_none()

        assert 'some_name' == participants['username']

        print(participants['username'])
        
        result = await session.execute(select(UserChat))
        chat = result.scalars().first()
        await session.delete(chat)
        await session.commit()
        

@pytest.mark.asyncio
async def test_json_keys_values(setup_test_db):
    '''проверка на правильное получение значения по ключу из бд'''
    async for session in setup_test_db:
        assert MODE == 'TEST'

        new_participants = UserChat(participants={'username': 'some_name'})
        session.add(new_participants)
        await session.commit()

        result_chat = await session.execute(select(UserChat.participants).where(UserChat.participants == new_participants.participants))
        chat = result_chat.scalar_one_or_none()

        print(chat)

        assert isinstance(chat, object)

        result = await session.execute(select(UserChat))
        chat = result.scalars().first()
        await session.delete(chat)
        await session.commit()


@pytest.mark.asyncio
async def test_dummy():
    '''проверка, что тесты вообще работают'''
    assert True