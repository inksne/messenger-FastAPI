from sqlalchemy import Integer, String, TIMESTAMP, Column, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

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
    authored_chats = relationship(
        'UserChat', foreign_keys='UserChat.auth_user', back_populates='auth_user_obj'
    )
    companion_chats = relationship(
        'UserChat', foreign_keys='UserChat.companion', back_populates='companion_obj'
    )



class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey(User.id), nullable=False)
    receiver_id = Column(Integer, ForeignKey(User.id), nullable=False)
    content = Column(String(length=512), nullable=False)
    sended_at = Column(TIMESTAMP, server_default=func.now())


    sender = relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    receiver = relationship('User', foreign_keys=[receiver_id], back_populates='received_messages')
    chat = relationship(
        'UserChat', 
          foreign_keys='UserChat.last_message_id', 
            back_populates='last_message'
    )



class UserChat(Base):
    __tablename__ = 'user_chats'
    id = Column(Integer, primary_key=True)
    auth_user = Column(Integer, ForeignKey(User.id), nullable=False)
    companion = Column(Integer, ForeignKey(User.id), nullable=False)
    last_message_id = Column(Integer, ForeignKey(Message.id))
    last_message_time = Column(TIMESTAMP, server_default=func.now())
    
    
    auth_user_obj = relationship('User', foreign_keys=[auth_user], back_populates='authored_chats')
    companion_obj = relationship('User', foreign_keys=[companion])
    last_message = relationship('Message', foreign_keys=[last_message_id], back_populates='chat')