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
    files = {"main_image": ("documento.pdf", BytesIO(file_content), "application/pdf")}
    data = {"title": "Mi Devlog", "content": "Avance 1", "user_id": test_user.id}
    
    response = client.post(f"/projects/{project.id}/devlogs", data=data, files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Solo se permiten imágenes JPG y PNG para la portada."

def test_upload_devlog_valid_image():
    db = next(override_get_db())
    test_user = db.query(models.User).filter(models.User.username == "test_devlog").first()
    project = db.query(models.Project).filter(models.Project.owner_id == test_user.id).first()
    
    file_content = b"fake png image"
    files = {"main_image": ("imagen.png", BytesIO(file_content), "image/png")}
    data = {"title": "Mi Primera Prueba", "content": "Testeando subida de devlog", "user_id": test_user.id}
    
    response = client.post(f"/projects/{project.id}/devlogs", data=data, files=files)
    assert response.status_code == 201
    
    response_data = response.json()
    assert response_data["project_id"] == project.id
    assert response_data["title"] == "Mi Primera Prueba"
    assert response_data["main_image_url"].startswith("/api/uploads/devlog_")
    assert response_data["main_image_url"].endswith(".png")

def test_upload_devlog_extra_image():
    db = next(override_get_db())
    test_user = db.query(models.User).filter(models.User.username == "test_devlog").first()
    project = db.query(models.Project).filter(models.Project.owner_id == test_user.id).first()
    devlog = db.query(models.Devlog).filter(models.Devlog.project_id == project.id).first()

    file_content = b"fake jpg extra image"
    files = {"image": ("extra.jpg", BytesIO(file_content), "image/jpeg")}
    data = {"user_id": test_user.id}
    
    response = client.post(f"/projects/devlogs/{devlog.id}/images", data=data, files=files)
    assert response.status_code == 201
    
    response_data = response.json()
    assert response_data["devlog_id"] == devlog.id
    assert response_data["image_url"].startswith("/api/uploads/gallery_")
    assert response_data["image_url"].endswith(".jpg")

    # Cleanup
    db.query(models.DevlogImage).filter(models.DevlogImage.devlog_id == devlog.id).delete()
    db.delete(devlog)
    db.delete(project)
    db.delete(test_user)
    db.commit()
