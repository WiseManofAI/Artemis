# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student")  # student, counsellor, admin
    full_name = Column(String, nullable=True)
    college = Column(String, nullable=True)
    enrollment = Column(String, nullable=True)
    linked_portal = Column(String, nullable=True)  # placeholder for college portal link
    created_at = Column(DateTime, default=datetime.utcnow)

    memory = relationship("UserMemory", back_populates="user")
    chats = relationship("ChatMessage", back_populates="user")
    risks = relationship("RiskScore", back_populates="user")


class UserMemory(Base):
    __tablename__ = "user_memories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    # visible memory: user's saved notes, progress, short chat snippets (if user saves)
    key = Column(String, index=True)
    value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="memory")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # user or bot
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chats")


class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    source = Column(String, default="automated")  # automated | clinician
    score = Column(Integer)  # 1-10
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)

    user = relationship("User", back_populates="risks")


class CounselorProfile(Base):
    __tablename__ = "counselor_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    qualifications = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
