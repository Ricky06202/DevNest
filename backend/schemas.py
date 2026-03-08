from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

# ==========================================
# REPLIES
# ==========================================
class ReplyBase(BaseModel):
    content: str = Field(..., description="Contenido o bloque de código propuesto")
    code_snippet: Optional[str] = None

class ReplyCreate(ReplyBase):
    pass

class ReplyResponse(ReplyBase):
    id: int
    thread_id: int
    author_id: int
    author_username: str
    author_karma: int
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
    author_username: str
    author_karma: int
    created_at: datetime
    snippets: List[ThreadSnippetResponse] = []
    replies: List[ReplyResponse] = []

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

class ReactionBase(BaseModel):
    emoji: str

class ReactionCreate(ReactionBase):
    pass

class ReactionResponse(ReactionBase):
    id: int
    devlog_id: int
    user_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DevlogImageResponse(BaseModel):
    id: int
    devlog_id: int
    image_url: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DevlogBase(BaseModel):
    title: str = Field(..., max_length=150)
    content: str
    main_image_url: str

class DevlogResponse(DevlogBase):
    id: int
    project_id: int
    created_at: datetime
    reactions: List[ReactionResponse] = []
    images: List[DevlogImageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    owner_username: str
    created_at: datetime
    devlogs: List[DevlogResponse] = []

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
    tech_stack: Optional[str] = None

class UserCreate(UserBase):
    # La contraseña solo viaja a la API en la creación/login, nunca de vuelta.
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    karma: int
    # Se hereda todo menos 'password', cumpliendo el requisito estricto
    
    model_config = ConfigDict(from_attributes=True)
