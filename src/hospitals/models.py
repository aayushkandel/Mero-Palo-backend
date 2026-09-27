from sqlalchemy import Column, BigInteger, String,Boolean ,DateTime
from sqlalchemy.sql import func
from src.utils.db import Base
from src.utils.uid import generate_uid
from sqlalchemy.orm import relationship

class Hospital(Base):
    __tablename__= "hospitals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    huid = Column(String(12),unique=True,nullable=False,default=generate_uid)
    name=Column(String(255),nullable=False)
    phone=Column(String(20),nullable=False, unique=True)
    registration_no=Column(String(255),nullable=False,unique=True)
    thumbnail_image=Column(String(255),nullable=False)
    is_authorized= Column(Boolean,nullable=False,default=False)
    created_at = Column(DateTime,server_default=func.now(),nullable=False)
    updated_at = Column(DateTime,server_default=func.now(),onupdate=func.now(),nullable=False )
    deleted_at=Column(DateTime(timezone=True),nullable=True)

    departments = relationship("Department",back_populates="hospital",cascade="all, delete-orphan")
    tokens = relationship("Token",back_populates="hospital")