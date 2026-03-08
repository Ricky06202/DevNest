from fastapi.testclient import TestClient
from main import app
from database import Base, engine, get_db
import models
import schemas
from sqlalchemy.orm import sessionmaker
from io import BytesIO

# Testing DB Setup
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_upload_devlog_invalid_extension():
    # Creamos un usuario de prueba directamente
    db = next(override_get_db())
    test_user = db.query(models.User).filter(models.User.username == "test_devlog").first()
    if not test_user:
        test_user = models.User(username="test_devlog", email="testdev@test.com", password_hash="hash")
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
    # Creamos un proyecto de prueba
    project = models.Project(title="Devlog Project", description="Test", owner_id=test_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Subida de archivo no valido
    file_content = b"fake pdf content"
    files = {"file": ("documento.pdf", BytesIO(file_content), "application/pdf")}
    
    response = client.post(f"/projects/{project.id}/devlogs?user_id={test_user.id}", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Solo se permiten imágenes JPG y PNG."

def test_upload_devlog_valid_image():
    db = next(override_get_db())
    test_user = db.query(models.User).filter(models.User.username == "test_devlog").first()
    project = db.query(models.Project).filter(models.Project.owner_id == test_user.id).first()
    
    file_content = b"fake png image"
    files = {"file": ("imagen.png", BytesIO(file_content), "image/png")}
    
    response = client.post(f"/projects/{project.id}/devlogs?user_id={test_user.id}", files=files)
    assert response.status_code == 201
    
    data = response.json()
    assert data["project_id"] == project.id
    assert data["image_url"].startswith("/uploads/proj_")
    assert data["image_url"].endswith(".png")
