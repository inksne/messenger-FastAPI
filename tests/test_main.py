import pytest
import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.future import select
from database.database import get_async_session, Base, engine, create_db_and_tables
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession


load_dotenv('.test.env')
MODE = os.getenv('MODE')
print(MODE)


@pytest.fixture(scope="function")
async def setup_test_db() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для создания базы данных и предоставления сессии для тестов."""
    assert MODE == 'TEST'
    await create_db_and_tables() 

    async with get_async_session() as session:
        try:
            yield session  
        finally:
            session.rollback()  
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_model_type(setup_test_db):
    """тест для проверки типа возвращаемого объекта из базы данных"""
    assert MODE == 'TEST'
    async for session in setup_test_db:  
        result = await session.execute(select(User))
        users = result.scalars().all()

    assert isinstance(users, list)


@pytest.mark.asyncio
async def test_create_user(setup_test_db):
    """тест для проверки создания пользователя в базе данных"""
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
    """тест для проверки создания пользователя в базе данных"""
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