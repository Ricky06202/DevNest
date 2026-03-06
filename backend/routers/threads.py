from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import database
import models
import schemas

router = APIRouter(
    prefix="/api/threads",
    tags=["Code Review Threads"]
)

@router.get("/", response_model=List[schemas.ThreadResponse])
def get_threads(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    """
    Obtiene todos los hilos de código paginados.
    """
    return db.query(models.Thread).offset(skip).limit(limit).all()

@router.get("/{thread_id}", response_model=schemas.ThreadResponse)
def get_thread(thread_id: int, db: Session = Depends(database.get_db)):
    """
    Obtiene un hilo específico con todas sus respuestas (cargadas vía relationship de SQLAlchemy).
    """
    thread = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Hilo no encontrado")
    return thread
def create_thread(thread: schemas.ThreadCreate, user_id: int, db: Session = Depends(database.get_db)):
    """
    Publica un nuevo fragmento de código para revisión (Muro interactivo).
    """
    author = db.query(models.User).filter(models.User.id == user_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    # Crear el hilo base
    db_thread = models.Thread(
        title=thread.title,
        content=thread.content,
        author_id=user_id
    )
    db.add(db_thread)
    db.flush() # Para obtener el ID antes de los snippets

    # Crear los snippets asociados
    for snippet_data in thread.snippets:
        db_snippet = models.ThreadSnippet(
            **snippet_data.model_dump(),
            thread_id=db_thread.id
        )
        db.add(db_snippet)

    db.commit()
    db.refresh(db_thread)
    return db_thread

@router.post("/{thread_id}/replies", response_model=schemas.ReplyResponse, status_code=status.HTTP_201_CREATED)
def add_reply(thread_id: int, reply: schemas.ReplyCreate, user_id: int, db: Session = Depends(database.get_db)):
    """
    Agrega una respuesta (bloque de código optimizado) a un hilo existente.
    """
    # Verificar que el hilo y el usuario existan
    thread = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Hilo no encontrado")
        
    author = db.query(models.User).filter(models.User.id == user_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_reply = models.Reply(**reply.model_dump(), thread_id=thread_id, author_id=user_id)
    db.add(db_reply)
    db.commit()
    db.refresh(db_reply)
    return db_reply

@router.put("/replies/{reply_id}/solution", response_model=schemas.ReplyResponse)
def mark_solution(reply_id: int, db: Session = Depends(database.get_db)):
    """
    Marca una respuesta específica como la 'Solución' u 'Óptima'.
    """
    reply = db.query(models.Reply).filter(models.Reply.id == reply_id).first()
    if not reply:
        raise HTTPException(status_code=404, detail="Respuesta no encontrada")
        
    reply.is_solution = True
    db.commit()
    db.refresh(reply)
    return reply
