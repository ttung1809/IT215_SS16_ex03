from datetime import datetime
from pydantic import BaseModel


# ---------- Input: yêu cầu đăng ký ----------
class RegistrationCreate(BaseModel):
    student_id: int
    workshop_id: int


# ---------- Thành phần lồng nhau cho output ----------
class WorkshopBrief(BaseModel):
    id: int
    title: str

    class Config:
        from_attributes = True


class StudentBrief(BaseModel):
    id: int
    full_name: str

    class Config:
        from_attributes = True


# ---------- Output: danh sách workshop của một sinh viên ----------
class StudentWorkshopsResponse(BaseModel):
    student_id: int
    full_name: str
    workshops: list[WorkshopBrief]

    class Config:
        from_attributes = True


# ---------- Output: danh sách sinh viên của một workshop ----------
class WorkshopStudentsResponse(BaseModel):
    workshop_id: int
    title: str
    students: list[StudentBrief]

    class Config:
        from_attributes = True


# ---------- (Tuỳ chọn) Output chi tiết một lượt đăng ký, có registered_at ----------
class RegistrationDetail(BaseModel):
    id: int
    student_id: int
    workshop_id: int
    registered_at: datetime

    class Config:
        from_attributes = True