from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)

    # Quan hệ 1-N với Registration: truy cập được registered_at của từng lượt đăng ký
    registrations = relationship(
        "Registration",
        back_populates="student"
    )

    # Quan hệ N-N tiện lợi với Workshop, thông qua bảng trung gian Registration
    workshops = relationship(
        "Workshop",
        secondary="registrations",
        back_populates="students",
        viewonly=True  # chỉ đọc — thao tác ghi phải đi qua Registration để lưu registered_at
    )


class Workshop(Base):
    __tablename__ = "workshops"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    maximum_participants = Column(Integer, nullable=False)

    # Quan hệ 1-N với Registration
    registrations = relationship(
        "Registration",
        back_populates="workshop"
    )

    # Quan hệ N-N tiện lợi với Student, thông qua bảng trung gian Registration
    students = relationship(
        "Student",
        secondary="registrations",
        back_populates="workshops",
        viewonly=True
    )


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)

    # Ràng buộc tham chiếu vật lý tới Student và Workshop
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    workshop_id = Column(Integer, ForeignKey("workshops.id"), nullable=False)

    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Đồng bộ hai chiều với Student và Workshop
    student = relationship("Student", back_populates="registrations")
    workshop = relationship("Workshop", back_populates="registrations")