from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func
from src.utils.db import Base
from src.utils.uid import generate_uid
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__= "users"

    id= Column(BigInteger,primary_key=True,autoincrement=True)
    uuid = Column(String(12),unique=True,nullable=False,default=generate_uid)
    name=Column(String(255),nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    address = Column(String(255), nullable=True)
    phone=Column(String(20),nullable=False,unique=True)
    role=Column(String(50),nullable=False)
    password=Column(String(255), nullable=False)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at = Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)    
    deleted_at = Column(DateTime(timezone=True),nullable=True)

    tokens = relationship("Token",back_populates="user")