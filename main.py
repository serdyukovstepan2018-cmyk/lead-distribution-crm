from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import Operator, Lead
import random
from typing import Optional
import models
import database

app = FastAPI()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Эндпоинт для создания оператора
@app.post("/operators/")
def create_operator(name: str, max_leads: int = 10, is_active: bool = True, db: Session = Depends(get_db)):

    new_operator = Operator(
        name = name,
        max_leads = max_leads,
        is_active = is_active
    )
    db.add(new_operator)
    db.commit()
    db.refresh(new_operator)

    return {
        "id": new_operator.id,
        "name": new_operator.name,
        "max_leads": new_operator.max_leads,
        "is_active": new_operator.is_active
    }

# Эндпоинт для получения всех операторов
@app.get("/operators/", response_model=List[dict])
def get_operators(db: Session = Depends(get_db)):
    operators = db.query(Operator).all()
    result = []
    for operator in operators:
        result.append({
            "id": operator.id,
            "name": operator.name,
            "max_leads": operator.max_leads,
            "is_active": operator.is_active
        })
    return result

@app.post('/leads/')
def create_lead(name:str, phone:str, email:str=None, db:Session=Depends(get_db)):
    existing_lead = db.query(models.Lead).filter(models.Lead.phone == phone).first()
    if existing_lead:
        raise HTTPException(status_code=400, detail="Lead with this phone already exists")
    new_lead = models.Lead(
        name = name, phone=phone, email=email
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    return {
        "id": new_lead.id,
        "name": new_lead.name,
        "phone": new_lead.phone,
        "email": new_lead.email
    }
@app.get('/leads/')
def get_lead(db:Session=Depends(get_db)):
    leads = db.query(models.Lead).all()
    result = []
    for lead in leads:
        result.append({
            "id": lead.id,
            "name": lead.name,
            "phone": lead.phone,
            "email": lead.email
        })
    return result

# Эндпоинт для создания источника
@app.post("/sources/")
def create_source(name: str, bot_id: str, description: str = None, db: Session = Depends(get_db)):
    existing_source = db.query(models.Source).filter(models.Source.bot_id == bot_id).first()
    if existing_source:
        raise HTTPException(status_code=400, detail="Source with this bot_id already exists")
    
    new_source = models.Source(
        name=name,
        bot_id=bot_id,
        description=description
    )
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    
    return {
        "id": new_source.id,
        "name": new_source.name,
        "bot_id": new_source.bot_id,
        "description": new_source.description
    }

# Эндпоинт для получения всех источников
@app.get("/sources/")
def get_sources(db: Session = Depends(get_db)):
    sources = db.query(models.Source).all()
    result = []
    for source in sources:
        result.append({
            "id": source.id,
            "name": source.name,
            "bot_id": source.bot_id,
            "description": source.description
        })
    return result

# Эндпоинт для настройки веса оператора для источника
@app.post("/distribution/")
def set_distribution(operator_id: int, source_id: int, weight: int = 10, db: Session = Depends(get_db)):
    operator = db.query(models.Operator).filter(models.Operator.id == operator_id).first()
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    existing_config = db.query(models.DistributionConfig).filter(
        models.DistributionConfig.operator_id == operator_id,
        models.DistributionConfig.source_id == source_id
    ).first()
    
    if existing_config:
        existing_config.weight = weight
    else:
        new_config = models.DistributionConfig(
            operator_id=operator_id,
            source_id=source_id,
            weight=weight
        )
        db.add(new_config)
    
    db.commit()
    
    return {
        "operator_id": operator_id,
        "source_id": source_id,
        "weight": weight,
    }

# Эндпоинт для регистрации обращения
@app.post("/contacts/")
def create_contact(lead_phone: str, source_id: int, lead_name: Optional[str] = None, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.phone == lead_phone).first()
    if not lead:
        if not lead_name:
            raise HTTPException(status_code=400, detail="Lead name required for new lead")
        lead = models.Lead(name=lead_name, phone=lead_phone)
        db.add(lead)
        db.commit()
        db.refresh(lead)
    
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    distributions = db.query(models.DistributionConfig).filter(
        models.DistributionConfig.source_id == source_id
    ).all()
    
    available_operators = []
    weights = []
    
    for dist in distributions:
        operator = db.query(models.Operator).filter(
            models.Operator.id == dist.operator_id,
            models.Operator.is_active == True
        ).first()
        
        if operator:
            current_load = db.query(models.Contact).filter(
                models.Contact.operator_id == operator.id
            ).count()
            
            if current_load < operator.max_leads:
                available_operators.append(operator)
                weights.append(dist.weight)
    
    selected_operator = None
    if available_operators and weights:
        selected_operator = random.choices(available_operators, weights=weights, k=1)[0]
    
    new_contact = models.Contact(
        lead_id=lead.id,
        source_id=source_id,
        operator_id=selected_operator.id if selected_operator else None
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    
    return {
        "contact_id": new_contact.id,
        "lead_id": lead.id,
        "lead_name": lead.name,
        "lead_phone": lead.phone,
        "source_id": source_id,
        "operator_id": selected_operator.id if selected_operator else None,
        "operator_name": selected_operator.name if selected_operator else None,
        "message": "Contact created successfully"
    }

# Просмотр всех обращений
@app.get("/contacts/")
def get_contacts(db: Session = Depends(get_db)):
    contacts = db.query(models.Contact).all()
    result = []
    for contact in contacts:
        result.append({
            "id": contact.id,
            "lead_id": contact.lead_id,
            "source_id": contact.source_id,
            "operator_id": contact.operator_id,
            "created_at": contact.created_at
        })
    return result

# Просмотр статистики
@app.get("/stats/")
def get_stats(db: Session = Depends(get_db)):
    operators_stats = []
    operators = db.query(models.Operator).all()
    
    for operator in operators:
        contacts_count = db.query(models.Contact).filter(
            models.Contact.operator_id == operator.id
        ).count()
        
        operators_stats.append({
            "operator_id": operator.id,
            "operator_name": operator.name,
            "max_leads": operator.max_leads,
            "current_load": contacts_count,
            "is_active": operator.is_active
        })
    
    return {
        "operators": operators_stats,
        "total_contacts": db.query(models.Contact).count(),
        "total_leads": db.query(models.Lead).count()
    }