import pytest
from typing import AsyncGenerator
from sqlalchemy.future import select
from database.models import User
from database.database import async_session_maker
from .test_config import MODE
from sqlalchemy.ext.asyncio import AsyncSession


print(MODE)


@pytest.fixture
async def setup_test_db(scope="function") -> AsyncGenerator[AsyncSession, None]:
    '''фикстура для создания базы данных и предоставления сессии для тестов'''
    assert MODE == 'TEST'
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.mark.asyncio
async def test_get_something(setup_test_db):
    assert MODE == 'TEST'
    async for session in setup_test_db: 
        result = await session.execute(select(User).where(User.id == 2))
        data = result.scalars().one_or_none()
        assert data == None


@pytest.mark.asyncio
async def test_model_type(setup_test_db):
    '''тест для проверки типа возвращаемого объекта из базы данных'''
    assert MODE == 'TEST'
    async for session in setup_test_db:  
        result = await session.execute(select(User))
        users = result.scalars().all()

    assert isinstance(users, list)


@pytest.mark.asyncio
async def test_create_user(setup_test_db):
    '''тест для проверки создания пользователя в базе данных'''
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
    '''тест для проверки создания пользователя в базе данных'''
    assert MODE == 'TEST'
    async for session in setup_test_db:  
        new_user = User(username="testuser", email="testuser@example.com", password="password")
        session.add(new_user)
        await session.commit()

        result = await session.execute(select(User))
        user = result.scalars().all()
        session.delete(user)
        session.commit()

        result = await session.execute(select(User))
        user = result.scalars().all()

        assert len(user) == 0


@pytest.mark.asyncio
async def test_dummy():
    '''проверка, что тесты вообще работаюют'''
    assert True