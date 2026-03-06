from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import database
import models
import schemas
import security

router = APIRouter(
    prefix="",
    tags=["Authentication"]
)

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """
    Registra un nuevo usuario en la base de datos MySQL.
    Comprueba si el username o el email ya existen.
    """
    # Verificar si el usuario ya existe (por email o username)
    db_user_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")
        
    db_user_username = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user_username:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso.")

    # Hashear la contraseña antes de guardar el usuario
    hashed_password = security.get_password_hash(user.password)
    
    # Crear la instancia del modelo SQLAlchemy (extraemos todo excepto 'password')
    user_data = user.model_dump(exclude={"password"})
    db_user = models.User(**user_data, password_hash=hashed_password)
    
    # Guardar en base de datos
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    """
    Inicia sesión usando 'username' y 'password'. Retorna un token JWT Bearer.
    Nota: OAuth2PasswordRequestForm usa el campo 'username' por defecto, pero nosotros comprobaremos en BD que sea su username.
    """
    # Buscar el usuario en la BD
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    # Validar que exista y que la contraseña coincida
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar el Token JWT
    access_token_expires = security.timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/debug/users")
def get_all_users(db: Session = Depends(database.get_db)):
    users = db.query(models.User).all()
    return [{"id": u.id, "username": u.username, "email": u.email} for u in users]
