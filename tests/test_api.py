import os
os.environ["DATABASE_URL"] = "sqlite:///./test_skilltrack.db"
os.environ["SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Career, CareerSkill, Skill

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    python = Skill(name="Python", category="Technical")
    db.add(python); db.flush()
    career = Career(name="AI/ML Engineer", description="Test career")
    db.add(career); db.flush()
    db.add(CareerSkill(career_id=career.id, skill_id=python.id, required_score=80, importance=1))
    db.commit()

client = TestClient(app)


def test_register_login_and_gap():
    response = client.post("/api/auth/register", json={"name":"Test Student", "email":"test@example.com", "password":"secret123"})
    assert response.status_code == 201
    token = client.post("/api/auth/login", json={"email":"test@example.com", "password":"secret123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    career_id = client.get("/api/careers").json()[0]["id"]
    assert client.put("/api/student/career-goal", headers=headers, json={"career_id": career_id}).status_code == 200
    skill_id = client.get("/api/skills").json()[0]["id"]
    assert client.put("/api/student/skills", headers=headers, json={"skill_id":skill_id,"current_score":45,"confidence_score":40}).status_code == 200
    gaps = client.get("/api/student/skill-gaps", headers=headers).json()
    assert gaps[0]["gap"] == 35
    assert gaps[0]["priority"] == "high"
