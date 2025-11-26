from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Operator(Base):
    __tablename__ = "operators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    max_leads = Column(Integer, default=10)  # лимит клиентов
    
    def __repr__(self):
        return f"Operator(id={self.id}, name='{self.name}', active={self.is_active}, max={self.max_leads})"
    
class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True)  # уникальный телефон
    email = Column(String, nullable=True)
    
    def __repr__(self):
        return f"Lead(id={self.id}, name='{self.name}', phone='{self.phone}')"
    
class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)        
    bot_id = Column(String, unique=True, nullable=False) 
    description = Column(String, nullable=True)
    
    def __repr__(self):
        return f"Source(id={self.id}, name='{self.name}', bot_id='{self.bot_id}')"

class DistributionConfig(Base):
    __tablename__ = "distribution_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    weight = Column(Integer, default=10)  
    

    operator = relationship("Operator")
    source = relationship("Source")
    
    def __repr__(self):
        return f"DistributionConfig(operator_id={self.operator_id}, source_id={self.source_id}, weight={self.weight})"
    
class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=True) 
    created_at = Column(String, default=lambda: str(datetime.now()))
    
  
    lead = relationship("Lead", backref="contacts")
    source = relationship("Source", backref="contacts") 
    operator = relationship("Operator", backref="contacts")
    
    def __repr__(self):
        return f"Contact(id={self.id}, lead_id={self.lead_id}, source_id={self.source_id}, operator_id={self.operator_id})"