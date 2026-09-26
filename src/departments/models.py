from sqlalchemy import Column, BigInteger, String, DateTime,ForeignKey
from sqlalchemy.sql import func
from src.utils.uid import generate_uid
from src.utils.db import Base

class Department(Base):
    __tablename__= "departments"

    id= Column(BigInteger,primary_key=True,autoincrement=True)
    duid=Column(String(12),unique=True, nullable=False, default=generate_uid)
    hospital_id=Column(BigInteger,ForeignKey("hospitals.id"),nullable=False)
    name=Column(String(255),nullable=False)
    phone=Column(String(20),nullable=True,unique=True)
    thumbnail_image=Column(String(255), nullable=False)
    created_at = Column(DateTime,server_default=func.now(),nullable=False)
    updated_at = Column(DateTime,server_default=func.now(),onupdate=func.now(),nullable=False )
    deleted_at=Column(DateTime(timezone=True),nullable=True)
