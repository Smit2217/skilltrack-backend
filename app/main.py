from datetime import date
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from . import models, schemas
from .auth import create_access_token, get_current_student, hash_password, verify_password
from .config import settings
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url, "http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def priority_for(gap: float, importance: float) -> str:
    weighted_gap = gap * importance
    if weighted_gap >= 30:
        return "high"
    if weighted_gap >= 15:
        return "medium"
    return "low"


ROADMAP_PATHS = {
    "statistics": ["Statistics Fundamentals", "Applied Statistics Project", "Machine Learning Fundamentals"],
    "machine learning": ["Python for ML", "Machine Learning Fundamentals", "ML Project", "Deep Learning", "Deployment"],
    "python": ["Python Fundamentals", "Object-Oriented Python", "Python Project", "Testing and Deployment"],
    "communication": ["Communication Fundamentals", "Presentation Practice", "Professional Communication"],
    "sql": ["SQL Fundamentals", "Relational Data Modeling", "Analytics Project", "Query Optimization"],
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=schemas.StudentOut, status_code=201)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(models.Student).where(models.Student.email == payload.email)):
        raise HTTPException(409, "Email is already registered")
    student = models.Student(**payload.model_dump(exclude={"password"}), password_hash=hash_password(payload.password))
    db.add(student); db.commit(); db.refresh(student)
    return student


@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    student = db.scalar(select(models.Student).where(models.Student.email == payload.email))
    if not student or not verify_password(payload.password, student.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return {"access_token": create_access_token(student.id), "token_type": "bearer"}


@app.get("/api/auth/me", response_model=schemas.StudentOut)
def me(student: models.Student = Depends(get_current_student)):
    return student


@app.get("/api/student/profile", response_model=schemas.StudentOut)
def profile(student: models.Student = Depends(get_current_student)):
    return student


@app.patch("/api/student/profile", response_model=schemas.StudentOut)
def update_profile(payload: schemas.StudentProfileUpdate, student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(student, key, value)
    db.commit(); db.refresh(student)
    return student


@app.get("/api/skills", response_model=list[schemas.SkillCatalogOut])
def list_skills(db: Session = Depends(get_db)):
    return db.scalars(select(models.Skill).order_by(models.Skill.name)).all()


@app.get("/api/student/skills", response_model=list[schemas.SkillOut])
def get_student_skills(student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    links = db.scalars(select(models.StudentSkill).where(models.StudentSkill.student_id == student.id)).all()
    return [schemas.SkillOut.model_validate(link).model_copy(update={"skill_name": link.skill.name, "category": link.skill.category}) for link in links]


@app.put("/api/student/skills", response_model=schemas.SkillOut)
def upsert_student_skill(payload: schemas.SkillCreate, student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    if not db.get(models.Skill, payload.skill_id): raise HTTPException(404, "Skill not found")
    link = db.scalar(select(models.StudentSkill).where(models.StudentSkill.student_id == student.id, models.StudentSkill.skill_id == payload.skill_id))
    if link: link.current_score = payload.current_score; link.confidence_score = payload.confidence_score
    else: link = models.StudentSkill(student_id=student.id, **payload.model_dump()); db.add(link)
    db.commit(); db.refresh(link)
    return schemas.SkillOut.model_validate(link).model_copy(update={"skill_name": link.skill.name, "category": link.skill.category})


@app.get("/api/student/projects", response_model=list[schemas.ProjectOut])
def projects(student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return db.scalars(select(models.Project).where(models.Project.student_id == student.id).order_by(desc(models.Project.date))).all()


@app.post("/api/student/projects", response_model=schemas.ProjectOut, status_code=201)
def add_project(payload: schemas.ProjectCreate, student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    item = models.Project(student_id=student.id, **payload.model_dump()); db.add(item); db.commit(); db.refresh(item); return item


@app.get("/api/student/certifications", response_model=list[schemas.CertificationOut])
def certifications(student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return db.scalars(select(models.Certification).where(models.Certification.student_id == student.id).order_by(desc(models.Certification.date))).all()


@app.post("/api/student/certifications", response_model=schemas.CertificationOut, status_code=201)
def add_certification(payload: schemas.CertificationCreate, student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    item = models.Certification(student_id=student.id, **payload.model_dump()); db.add(item); db.commit(); db.refresh(item); return item


@app.get("/api/careers", response_model=list[schemas.CareerOut])
def careers(db: Session = Depends(get_db)):
    return db.scalars(select(models.Career).order_by(models.Career.name)).all()


@app.get("/api/careers/{career_id}/skills", response_model=list[schemas.CareerSkillOut])
def career_skills(career_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Career, career_id): raise HTTPException(404, "Career not found")
    links = db.scalars(select(models.CareerSkill).where(models.CareerSkill.career_id == career_id)).all()
    return [{"skill_id": x.skill_id, "skill_name": x.skill.name, "required_score": x.required_score, "importance": x.importance} for x in links]


@app.put("/api/student/career-goal", response_model=schemas.StudentOut)
def set_career_goal(payload: schemas.CareerGoalRequest, student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    career = db.get(models.Career, payload.career_id)
    if not career: raise HTTPException(404, "Career not found")
    student.career_goal = career.name; db.commit(); db.refresh(student); return student


@app.post("/api/student/assessments", response_model=schemas.AssessmentOut, status_code=201)
def add_assessment(payload: schemas.AssessmentCreate, student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    if not db.get(models.Skill, payload.skill_id): raise HTTPException(404, "Skill not found")
    item = models.Assessment(student_id=student.id, date=payload.date or date.today(), **payload.model_dump(exclude={"date"})); db.add(item)
    link = db.scalar(select(models.StudentSkill).where(models.StudentSkill.student_id == student.id, models.StudentSkill.skill_id == payload.skill_id))
    if link: link.current_score = payload.score
    else: db.add(models.StudentSkill(student_id=student.id, skill_id=payload.skill_id, current_score=payload.score, confidence_score=0))
    db.add(models.SkillProgress(student_id=student.id, skill_id=payload.skill_id, score=payload.score, date=item.date)); db.commit(); db.refresh(item); return item


@app.get("/api/student/assessments", response_model=list[schemas.AssessmentOut])
def assessment_history(student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return db.scalars(select(models.Assessment).where(models.Assessment.student_id == student.id).order_by(desc(models.Assessment.date))).all()


def calculate_gaps(student: models.Student, db: Session):
    career = db.scalar(select(models.Career).where(models.Career.name == student.career_goal)) if student.career_goal else None
    if not career: raise HTTPException(400, "Set a career goal first")
    current = {x.skill_id: x.current_score for x in student.skills}
    result = []
    for req in career.skills:
        score = current.get(req.skill_id, 0); gap = max(req.required_score - score, 0)
        result.append(schemas.GapOut(skill_id=req.skill_id, skill_name=req.skill.name, current_score=score, required_score=req.required_score, gap=gap, importance=req.importance, priority=priority_for(gap, req.importance), status="good" if gap == 0 else "needs_improvement"))
    return sorted(result, key=lambda x: (-x.gap * x.importance, x.skill_name))


@app.get("/api/student/skill-gaps", response_model=list[schemas.GapOut])
def skill_gaps(student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return calculate_gaps(student, db)


@app.get("/api/student/roadmap", response_model=list[schemas.RoadmapStep])
def roadmap(student: models.Student = Depends(get_current_student), db: Session = Depends(get_db)):
    gaps = [x for x in calculate_gaps(student, db) if x.gap > 0]
    return [schemas.RoadmapStep(skill_name=x.skill_name, priority=x.priority, steps=ROADMAP_PATHS.get(x.skill_name.lower(), [f"{x.skill_name} Fundamentals", f"{x.skill_name} Practice Project", f"Advanced {x.skill_name}"])) for x in gaps]


@app.get("/api/faculty/students", response_model=list[schemas.StudentOut])
def faculty_students(db: Session = Depends(get_db)):
    return db.scalars(select(models.Student).order_by(models.Student.name)).all()


@app.get("/api/faculty/students/{student_id}/skills", response_model=list[schemas.SkillOut])
def faculty_student_skills(student_id: int, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if not student: raise HTTPException(404, "Student not found")
    return [schemas.SkillOut.model_validate(x).model_copy(update={"skill_name": x.skill.name, "category": x.skill.category}) for x in student.skills]


@app.get("/api/faculty/students/{student_id}/progress", response_model=list[schemas.ProgressOut])
def faculty_student_progress(student_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Student, student_id): raise HTTPException(404, "Student not found")
    rows = db.scalars(select(models.SkillProgress).where(models.SkillProgress.student_id == student_id).order_by(models.SkillProgress.skill_id, desc(models.SkillProgress.date))).all()
    grouped = {}
    for row in rows:
        if row.skill_id not in grouped: grouped[row.skill_id] = [row]
        elif len(grouped[row.skill_id]) < 2: grouped[row.skill_id].append(row)
    return [schemas.ProgressOut(skill_id=k, skill_name=v[0].skill.name, latest_score=v[0].score, previous_score=v[1].score if len(v)>1 else None, change=(v[0].score-v[1].score) if len(v)>1 else None, last_updated=v[0].date, stagnant=len(v)>1 and v[0].score <= v[1].score) for k,v in grouped.items()]


@app.get("/api/faculty/students/low-progress", response_model=list[schemas.StudentOut])
def low_progress(db: Session = Depends(get_db)):
    students = db.scalars(select(models.Student)).all(); low = []
    for student in students:
        rows = db.scalars(select(models.SkillProgress).where(models.SkillProgress.student_id == student.id).order_by(desc(models.SkillProgress.date))).all()
        if len(rows) >= 2 and rows[0].score <= rows[1].score: low.append(student)
    return low


@app.get("/api/faculty/students/{student_id}/skill-gaps", response_model=list[schemas.GapOut])
def faculty_skill_gaps(student_id: int, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if not student: raise HTTPException(404, "Student not found")
    return calculate_gaps(student, db)
