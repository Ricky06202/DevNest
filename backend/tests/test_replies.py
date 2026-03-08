from fastapi.testclient import TestClient
from main import app
from database import Base, engine, get_db
import models
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_reply_with_and_without_code():
    db = next(override_get_db())
    test_user = db.query(models.User).filter(models.User.username == "test_reply").first()
    if not test_user:
        test_user = models.User(username="test_reply", email="testreply@test.com", password_hash="hash")
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
    thread = models.Thread(title="Test Thread", content="Need help", author_id=test_user.id)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    
    # Text-only Reply
    payload_text = {
        "content": "Solamente un mensaje de texto plano."
    }
    response_text = client.post(f"/threads/{thread.id}/replies?user_id={test_user.id}", json=payload_text)
    assert response_text.status_code == 201
    assert response_text.json()["content"] == payload_text["content"]
    assert response_text.json()["code_snippet"] is None
    
    # Text + Code Reply
    payload_code = {
        "content": "Aca te dejo el script que pides",
        "code_snippet": "print('Hola Mundo')"
    }
    response_code = client.post(f"/threads/{thread.id}/replies?user_id={test_user.id}", json=payload_code)
    assert response_code.status_code == 201
    assert response_code.json()["content"] == payload_code["content"]
    assert response_code.json()["code_snippet"] == payload_code["code_snippet"]

    # Cleanup (Optional)
    db.query(models.Reply).filter(models.Reply.thread_id == thread.id).delete()
    db.delete(thread)
    db.delete(test_user)
    db.commit()
