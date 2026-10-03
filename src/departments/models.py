from sqlalchemy import Column, BigInteger, String, DateTime,ForeignKey,Time,Date,Integer
from sqlalchemy.sql import func
from src.utils.uid import generate_uid
from src.utils.db import Base
from sqlalchemy.orm import relationship
from src.departments.dtos import OpenStatus


class Department(Base):
    __tablename__= "departments"

    id= Column(BigInteger,primary_key=True,autoincrement=True)
    duid=Column(String(12),unique=True, nullable=False, default=generate_uid)
    hospital_id=Column(BigInteger,ForeignKey("hospitals.id"),nullable=False)
    name=Column(String(255),nullable=False)
    phone=Column(String(20),nullable=True)
    department_room_no=Column(String(50),nullable=True)
    password=Column(String(255),nullable=False)
    created_at = Column(DateTime,server_default=func.now(),nullable=False)
    updated_at = Column(DateTime,server_default=func.now(),onupdate=func.now(),nullable=False )
    deleted_at=Column(DateTime(timezone=True),nullable=True)



    hospital = relationship("Hospital",back_populates="departments")
    tokens = relationship("Token",back_populates="department")
    schedules = relationship("Schedule",back_populates="department")

class Schedule(Base):
            __tablename__="schedules"
    
            id= Column(BigInteger,primary_key=True,autoincrement=True)
            suid=Column(String(12),unique=True,nullable=False,default=generate_uid)
            hospital_id=Column(BigInteger,ForeignKey("hospitals.id"),nullable=False)
            date=Column(Date,nullable=True)
            open_status = Column(Integer,nullable=False,default=OpenStatus.Open)
            department_id=Column(BigInteger,ForeignKey("departments.id"),nullable=False)
            registration_start=Column(Time,nullable=True)
            registration_close=Column(Time,nullable=True)
            token_start=Column(Time,nullable=True)
            created_at = Column(DateTime(timezone=True),nullable=True)
            updated_at=Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)    
    
            department = relationship("Department",back_populates="schedules")
            hospital = relationship("Hospital",back_populates="schedules")