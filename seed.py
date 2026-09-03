from sqlalchemy import select
from app.database import SessionLocal
from app.models import Career, CareerSkill, Skill

SKILLS = [
    ("Python", "Technical", "Programming with Python."),
    ("Machine Learning", "Technical", "Core supervised and unsupervised learning concepts."),
    ("Statistics", "Technical", "Probability, inference, and descriptive statistics."),
    ("SQL", "Technical", "Querying and modeling relational data."),
    ("Communication", "Soft Skill", "Clear written, verbal, and presentation communication."),
    ("Git", "Technical", "Version control and collaborative development."),
    ("Cloud Computing", "Technical", "Cloud infrastructure and deployment fundamentals."),
    ("Cybersecurity", "Technical", "Security principles, threats, and defensive practices."),
]
CAREERS = {
    "Software Developer": [("Python", 70, 1.0), ("SQL", 60, .8), ("Git", 65, .8), ("Communication", 60, .6)],
    "AI/ML Engineer": [("Python", 80, 1.0), ("Machine Learning", 80, 1.0), ("Statistics", 70, .9), ("SQL", 60, .6)],
    "Data Scientist": [("Python", 75, 1.0), ("Machine Learning", 70, .9), ("Statistics", 80, 1.0), ("SQL", 75, .9)],
    "Cybersecurity Analyst": [("Cybersecurity", 80, 1.0), ("Python", 60, .6), ("Communication", 65, .7)],
    "Cloud Engineer": [("Cloud Computing", 80, 1.0), ("Python", 65, .7), ("Git", 65, .6), ("Cybersecurity", 60, .7)],
}

with SessionLocal() as db:
    skills = {}
    for name, category, description in SKILLS:
        skill = db.scalar(select(Skill).where(Skill.name == name)) or Skill(name=name, category=category, description=description)
        db.add(skill); db.flush(); skills[name] = skill
    for name, requirements in CAREERS.items():
        career = db.scalar(select(Career).where(Career.name == name)) or Career(name=name, description=f"Skills and learning path for {name}.")
        db.add(career); db.flush()
        existing = {link.skill_id for link in career.skills}
        for skill_name, required_score, importance in requirements:
            if skills[skill_name].id not in existing:
                db.add(CareerSkill(career_id=career.id, skill_id=skills[skill_name].id, required_score=required_score, importance=importance))
    db.commit()
print("Starter data loaded.")
