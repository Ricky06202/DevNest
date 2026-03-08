from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
import uuid
from datetime import datetime

import database
import models
import schemas

# Usar el router sin prefijo para que encaje como "api/projects" o simlilar desde main
router = APIRouter(
    prefix="/projects",
    tags=["Projects (Matchmaking Radar)"]
)

@router.get("/", response_model=List[schemas.ProjectResponse])
def get_projects(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    """
    Obtiene todos los proyectos del Radar (Matchmaking) paginados, más recientes primero.
    """
    projects = db.query(models.Project).order_by(models.Project.created_at.desc()).offset(skip).limit(limit).all()
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

@router.post("/{project_id}/devlogs", response_model=schemas.DevlogResponse, status_code=status.HTTP_201_CREATED)
def create_devlog_post(
    project_id: int, 
    title: str = Form(...),
    content: str = Form(...),
    user_id: int = Form(...),
    main_image: UploadFile = File(...), 
    db: Session = Depends(database.get_db)
):
    """
    Sube un nuevo post de avance (Devlog) con título, texto y una imagen principal.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
    if project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Solo el creador puede publicar devlogs")
        
    ext = main_image.filename.split(".")[-1].lower() if main_image.filename else ""
    if ext not in ["jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Solo se permiten imágenes JPG y PNG para la portada.")
        
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"devlog_{project_id}_{timestamp}_{unique_id}.{ext}"
    filepath = os.path.join("uploads", filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(main_image.file, buffer)
        
    main_image_url = f"/api/uploads/{filename}"
    
    devlog = models.Devlog(
        project_id=project_id, 
        title=title,
        content=content,
        main_image_url=main_image_url
    )
    db.add(devlog)
    db.commit()
    db.refresh(devlog)
    return devlog

@router.post("/devlogs/{devlog_id}/images", response_model=schemas.DevlogImageResponse, status_code=status.HTTP_201_CREATED)
def upload_devlog_extra_image(
    devlog_id: int, 
    user_id: int = Form(...),
    image: UploadFile = File(...), 
    db: Session = Depends(database.get_db)
):
    """
    Sube una foto adicional a la galería de un Devlog específico.
    """
    devlog = db.query(models.Devlog).filter(models.Devlog.id == devlog_id).first()
    if not devlog:
        raise HTTPException(status_code=404, detail="Devlog no encontrado")
        
    project = db.query(models.Project).filter(models.Project.id == devlog.project_id).first()
    if not project or project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Sin permisos para modificar este devlog")

    ext = image.filename.split(".")[-1].lower() if image.filename else ""
    if ext not in ["jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Solo imágenes JPG y PNG.")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"gallery_{devlog_id}_{timestamp}_{unique_id}.{ext}"
    filepath = os.path.join("uploads", filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
        
    image_url = f"/api/uploads/{filename}"
    
    devlog_image = models.DevlogImage(devlog_id=devlog_id, image_url=image_url)
    db.add(devlog_image)
    db.commit()
    db.refresh(devlog_image)
    return devlog_image

@router.post("/devlogs/{devlog_id}/react", response_model=schemas.ReactionResponse, status_code=status.HTTP_201_CREATED)
def react_to_devlog(devlog_id: int, user_id: int, emoji: str = "🔥", db: Session = Depends(database.get_db)):
    """
    Agrega una reacción a un devlog existente. Si el usuario ya reaccionó con el mismo emoji, se ignora.
    """
    devlog = db.query(models.Devlog).filter(models.Devlog.id == devlog_id).first()
    if not devlog:
        raise HTTPException(status_code=404, detail="Devlog no encontrado")
        
    existing_reaction = db.query(models.Reaction).filter(
        models.Reaction.devlog_id == devlog_id,
        models.Reaction.user_id == user_id,
        models.Reaction.emoji == emoji
    ).first()
    
    if existing_reaction:
        return existing_reaction
        
    reaction = models.Reaction(devlog_id=devlog_id, user_id=user_id, emoji=emoji)
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    return reaction
