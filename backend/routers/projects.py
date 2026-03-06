from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import database
import models
import schemas

# Usar el router sin prefijo para que encaje como "api/projects" o simlilar desde main
router = APIRouter(
    prefix="/api/projects",
    tags=["Projects (Matchmaking Radar)"]
)

@router.get("/", response_model=List[schemas.ProjectResponse])
def get_projects(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    """
    Obtiene todos los proyectos del Radar (Matchmaking) paginados.
    """
    projects = db.query(models.Project).offset(skip).limit(limit).all()
    return projects

@router.post("/", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate, user_id: int, db: Session = Depends(database.get_db)):
    """
    Crea un nuevo proyecto para buscar equipo.
    NOTA TEMPORAL: user_id se pide por parámetro para pruebas hasta conectar el JWT fully-fledged con @Depends.
    """
    # Verificar que el usuario (owner) existe
    owner = db.query(models.User).filter(models.User.id == user_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    db_project = models.Project(**project.model_dump(), owner_id=user_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(database.get_db)):
    """
    Obtiene un proyecto específico por su ID.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project

@router.put("/{project_id}", response_model=schemas.ProjectResponse)
def update_project(project_id: int, project_update: schemas.ProjectCreate, user_id: int, db: Session = Depends(database.get_db)):
    """
    Actualiza los detalles de un proyecto.
    """
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
    # Verificar que el usuario es el dueño (dueño_id)
    if db_project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para editar este proyecto")

    # Actualizar campos
    db_project.title = project_update.title
    db_project.description = project_update.description
    db_project.roles_sought = project_update.roles_sought
    db_project.is_open = project_update.is_open

    db.commit()
    db.refresh(db_project)
    return db_project

@router.put("/{project_id}/close", response_model=schemas.ProjectResponse)
def close_project(project_id: int, db: Session = Depends(database.get_db)):
    """
    Marca un proyecto como cerrado (ej. cuando ya se armó el equipo).
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
    project.is_open = False
    db.commit()
    db.refresh(project)
    return project
