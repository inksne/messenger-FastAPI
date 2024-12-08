from sqlalchemy import Integer, String, TIMESTAMP, Column, Boolean, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass


user_chat_association = Table(
    'user_chat_participants', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('chat_id', Integer, ForeignKey('user_chats.id'), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(length=24), nullable=False)
    email = Column(String)
    password = Column(String(length=1024), nullable=False)
    registered_at = Column(TIMESTAMP, server_default=func.now())
    active = Column(Boolean, default = True, nullable=False)


    sent_messages = relationship('Message', foreign_keys='Message.sender_id', back_populates='sender')
    received_messages = relationship('Message', foreign_keys='Message.receiver_id', back_populates='receiver')
    chats = relationship('UserChat', secondary=user_chat_association, back_populates='participants')


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey(User.id), nullable=False)
    receiver_id = Column(Integer, ForeignKey(User.id), nullable=False)
    content = Column(String(length=512), nullable=False)
    sended_at = Column(TIMESTAMP, server_default=func.now())


    sender = relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    receiver = relationship('User', foreign_keys=[receiver_id], back_populates='received_messages')
    chat = relationship('UserChat', back_populates='messages')


class UserChat(Base):
    __tablename__ = 'user_chats'
    id = Column(Integer, primary_key=True)
    last_message_id = Column(Integer, ForeignKey(Message.id))
    last_message_time = Column(TIMESTAMP, server_default=func.now())
    
    participants = relationship('User', secondary=user_chat_association, back_populates='chats')
    last_message = relationship('Message', foreign_keys=[last_message_id])
    messages = relationship('Message', back_populates='chat')