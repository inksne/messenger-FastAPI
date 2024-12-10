from sqlalchemy import Integer, String, TIMESTAMP, Column, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(length=24), unique=True, nullable=False)
    email = Column(String)
    password = Column(String(length=1024), nullable=False)
    registered_at = Column(TIMESTAMP, server_default=func.now())
    active = Column(Boolean, default=True, nullable=False)

    sent_messages = relationship('Message', back_populates='author')


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    author_username = Column(String(length=24), ForeignKey('users.username'), nullable=False)
    content = Column(String(length=512), nullable=False)
    sended_at = Column(TIMESTAMP, server_default=func.now())
    chat_id = Column(Integer, ForeignKey('user_chats.id'), nullable=False)

    author = relationship('User', back_populates='sent_messages')
    chat = relationship('UserChat', back_populates='messages', foreign_keys=[chat_id])  


class UserChat(Base):
    __tablename__ = 'user_chats'
    id = Column(Integer, primary_key=True)
    participants = Column(JSON)
    last_message_time = Column(TIMESTAMP, server_default=func.now())

    messages = relationship('Message', back_populates='chat', lazy='dynamic')  