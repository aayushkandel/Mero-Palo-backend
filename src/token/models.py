from sqlalchemy import Column,BigInteger,String,Integer,DateTime,Boolean,ForeignKey,Time,Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.utils.db import Base
from src.utils.uid import generate_uid


class Token(Base):
    __tablename__ = "tokens"

    id = Column(BigInteger,primary_key=True,autoincrement=True)
    tuid = Column(String(12),unique=True,nullable=False,default=generate_uid)
    user_id = Column(BigInteger,ForeignKey("users.id"),nullable=False)
    hospital_id = Column(BigInteger,ForeignKey("hospitals.id"),nullable=False)
    department_id = Column(BigInteger,ForeignKey("departments.id"),nullable=False)
    patient_name=Column(String(255),nullable=False)
    patient_address=Column(String(255),nullable=False)
    patient_age=Column(Integer,nullable=False)
    patient_phone=Column(String(20),nullable=False)
    token = Column(String(15),nullable=False)
    dates=Column(Date,nullable=False)
    started_at = Column(DateTime(timezone=True),nullable=True)
    ended_at = Column(DateTime(timezone=True),nullable=True)
    expected_time = Column(Time,nullable=True)
    actual_time = Column(Time,nullable=True)
    waiting_time=Column(Time,nullable=True)
    token_status = Column(String(20),nullable=False,default="waiting")
    deleted_by_user =Column(DateTime(timezone=True),nullable=True)
    deleted_by_department =Column(DateTime(timezone=True),nullable=True)


    # Relationships

    user = relationship("User",back_populates="tokens")

    hospital = relationship("Hospital",back_populates="tokens")
    
    department = relationship("Department",back_populates="tokens")

    
