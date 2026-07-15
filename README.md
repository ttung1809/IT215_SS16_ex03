# Phân tích và thiết kế mô hình quan hệ Đăng ký Workshop

## Phần 1: Thiết kế cơ sở dữ liệu và Phân tích quan hệ

### 1.1. Sơ đồ thực thể liên kết (ERD)

```
┌───────────────┐          ┌──────────────────┐          ┌───────────────┐
│    Student    │          │   Registration    │          │   Workshop    │
├───────────────┤   1    N ├────────────────────┤ N    1   ├───────────────┤
│ id (PK)       │──────────│ id (PK)            │──────────│ id (PK)       │
│ student_code  │          │ student_id (FK)    │          │ title         │
│ full_name     │          │ workshop_id (FK)   │          │ maximum_      │
│ email         │          │ registered_at      │          │  participants │
└───────────────┘          └────────────────────┘          └───────────────┘
        \                                                          /
         \___________________ N - N (qua secondary) ______________/
```

Diễn giải bằng lời:
- `Student` 1 — N `Registration`: một sinh viên có thể có nhiều lượt đăng ký.
- `Workshop` 1 — N `Registration`: một workshop có thể có nhiều lượt đăng ký.
- Kết quả tổng hợp: `Student` N — N `Workshop`, được "bắc cầu" thông qua `Registration`.

### 1.2. Xác định vị trí khóa ngoại

Bảng con (Child Table) giữ khóa ngoại trong mối quan hệ này là **`Registration`** — nó giữ cả hai khóa ngoại `student_id` và `workshop_id`, cùng trỏ về khóa chính của `Student` và `Workshop`.

**Lý do dưới góc độ toàn vẹn dữ liệu:**
- Trong quan hệ N-N thuần túy, không thể đặt FK ở `Student` hay `Workshop` vì mỗi cột chỉ lưu được **một** giá trị tham chiếu — trong khi một sinh viên có thể đăng ký nhiều workshop và ngược lại. Đặt FK ở 2 bảng chính sẽ giới hạn quan hệ về 1-N, sai với bản chất bài toán.
- Khi FK được đặt tại `Registration` và được khai báo đúng ràng buộc (`ForeignKey` trỏ về `students.id` và `workshops.id`), tầng CSDL sẽ **tự động từ chối** mọi bản ghi đăng ký có `student_id` hoặc `workshop_id` không tồn tại trong bảng gốc — đây chính là cách giải quyết triệt để vấn đề "dữ liệu đăng ký rác" nêu trong bối cảnh bài toán, thay vì chỉ kiểm tra ở tầng ứng dụng (dễ bị bỏ sót hoặc bypass).
- Mỗi dòng trong `Registration` còn đại diện cho một "sự kiện nghiệp vụ" cụ thể (một lượt đăng ký, có `registered_at` riêng) — điều này tự nhiên đòi hỏi nó phải là một bảng độc lập giữ khóa ngoại, không thể gộp vào `Student` hay `Workshop`.

### 1.3. Phân tích sự đánh đổi: `secondary` vs. hai quan hệ 1-N tuần tự

| Khía cạnh | Dùng `secondary` | Dùng 2 quan hệ 1-N tuần tự |
|---|---|---|
| Cách truy xuất | `student.workshops` trả thẳng `list[Workshop]` | Phải duyệt: `[r.workshop for r in student.registrations]` |
| Truy cập cột phụ của bảng trung gian (`registered_at`) | Không thể lấy trực tiếp qua `student.workshops` — mất thông tin về thời điểm đăng ký của từng cặp | Truy cập được dễ dàng qua từng object `Registration` (`registration.registered_at`) |
| Độ phù hợp với bài toán này | Phù hợp cho truy xuất nhanh, đúng với yêu cầu output ở Mục 5 (chỉ cần `id`, `title` / `id`, `full_name`) | Cần thiết nếu sau này phải hiển thị thêm `registered_at` trong response |
| Số lượng thuộc tính relationship cần khai báo | Ít hơn (chỉ cần khai báo N-N qua `secondary`) | Nhiều hơn (cần cả `student.registrations`, `workshop.registrations`, và duyệt thủ công) |

**Kết luận cho bài toán này:** Vì `Registration` có cột nghiệp vụ riêng (`registered_at`) mà `secondary` không cho phép truy cập tiện lợi, giải pháp tối ưu là **kết hợp cả hai**: vẫn khai báo `Registration` là Model đầy đủ với `relationship` 1-N riêng (để có thể truy vấn `registered_at` khi cần), đồng thời khai báo thêm quan hệ N-N tiện lợi bằng `secondary="registrations"` giữa `Student` và `Workshop` để phục vụ đúng yêu cầu "truy xuất gián tiếp N-N" ở Mục 4 và định dạng output ở Mục 5 (chỉ cần danh sách workshop/sinh viên, không cần `registered_at`).

---

## Phần 2: Triển khai source code khung

### 1. database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Chuỗi kết nối giả định tới MySQL
# Định dạng: mysql+pymysql://<user>:<password>@<host>:<port>/<database>
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/workshop_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency cung cấp một phiên làm việc (session) cho mỗi request,
    sử dụng cơ chế yield để đảm bảo session luôn được đóng lại
    sau khi xử lý xong, kể cả khi có lỗi xảy ra.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 2. models.py

```python
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
```

### 3. schemas.py

```python
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
```

### Ghi chú thiết kế đáng chú ý cho sinh viên

- **Vì sao có cả `registrations` và `workshops` (hoặc `students`) trên cùng một Model?** Đây là điểm mấu chốt của bài — không phải lúc nào cũng chọn *một trong hai* cách (secondary hay 1-N tuần tự); trong thực tế, nhiều hệ thống dùng **cả hai song song**: quan hệ 1-N để giữ quyền truy cập đầy đủ vào bảng trung gian (kể cả cột phụ), và quan hệ N-N qua `secondary` chỉ để đọc nhanh khi không cần cột phụ.
- **`viewonly=True`** trên các relationship `secondary` là chi tiết kỹ thuật quan trọng: vì `Registration` có cột bắt buộc `registered_at`, SQLAlchemy sẽ không biết điền giá trị này nếu lập trình viên cố ghi dữ liệu qua `student.workshops.append(...)`. Đặt `viewonly=True` để bắt buộc mọi thao tác *ghi* phải đi qua `Registration` (nơi `registered_at` được xử lý đúng), tránh lỗi tiềm ẩn khi insert.
- Việc tách schema `WorkshopBrief` / `StudentBrief` riêng khỏi các Model chính thể hiện đúng nguyên tắc **Pydantic Schema mô tả hình dạng dữ liệu ra/vào của API, không nhất thiết trùng khớp 1-1 với cấu trúc bảng CSDL** — output chỉ cần `id`, `title`/`full_name`, không cần export toàn bộ các trường của Model.