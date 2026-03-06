from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

# ==========================================
# REPLIES
# ==========================================
class ReplyBase(BaseModel):
    content: str = Field(..., description="Contenido o bloque de código propuesto")

class ReplyCreate(ReplyBase):
    pass

class ReplyResponse(ReplyBase):
    id: int
    thread_id: int
    author_id: int
    is_solution: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# THREAD SNIPPETS (Multi-file support)
# ==========================================
class ThreadSnippetBase(BaseModel):
    filename: str = Field(..., max_length=100)
    language: str = Field(..., max_length=50)
    code: str

class ThreadSnippetCreate(ThreadSnippetBase):
    pass

class ThreadSnippetResponse(ThreadSnippetBase):
    id: int
    thread_id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# THREADS (Hilos de código)
# ==========================================
class ThreadBase(BaseModel):
    title: str = Field(..., max_length=150)
    content: str

class ThreadCreate(ThreadBase):
    snippets: List[ThreadSnippetCreate] = []

class ThreadResponse(ThreadBase):
    id: int
    author_id: int
    created_at: datetime
    snippets: List[ThreadSnippetResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# PROJECTS (Radar de matchmaking)
# ==========================================
class ProjectBase(BaseModel):
    title: str = Field(..., max_length=150)
    description: str
    roles_sought: Optional[str] = Field(default=None, description="Ej: 'Frontend, Backend'")
    is_open: bool = True

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# USERS
# ==========================================
class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    email: EmailStr
    bio: Optional[str] = None
    github_username: Optional[str] = None
    experience_level: Optional[str] = None

class UserCreate(UserBase):
    # La contraseña solo viaja a la API en la creación/login, nunca de vuelta.
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    # Se hereda todo menos 'password', cumpliendo el requisito estricto
    
    model_config = ConfigDict(from_attributes=True)
