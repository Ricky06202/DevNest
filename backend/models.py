from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    github_username = Column(String(100), nullable=True)
    experience_level = Column(String(50), nullable=True)  # Ej. "Junior", "Mid", "Senior"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones One-to-Many
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    threads = relationship("Thread", back_populates="author", cascade="all, delete-orphan")
    replies = relationship("Reply", back_populates="author", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    roles_sought = Column(String(255), nullable=True)  # Ej. "Frontend, Backend" o JSON
    is_open = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación inversa
    owner = relationship("User", back_populates="projects")

class Thread(Base):
    __tablename__ = "threads"
    
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    content = Column(Text, nullable=False)
    code_language = Column(String(50), nullable=True)  # Para Monaco Editor
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    author = relationship("User", back_populates="threads")
    replies = relationship("Reply", back_populates="thread", cascade="all, delete-orphan")

class Reply(Base):
    __tablename__ = "replies"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_solution = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones inversas
    thread = relationship("Thread", back_populates="replies")
    author = relationship("User", back_populates="replies")
