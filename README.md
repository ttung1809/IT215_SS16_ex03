Đây là bài thiết kế hệ thống nên giảng viên không chấm việc "code được", mà chấm **phân tích → thiết kế → triển khai**. Dưới đây là một phương án hoàn chỉnh.

---

# PHẦN 1: THIẾT KẾ KIẾN TRÚC

## 7.1. Phân tích nhu cầu

### Vấn đề của khách hàng

Hiện tại việc quản lý workshop bằng Google Form và Excel dẫn đến:

* Sinh viên đăng ký trùng workshop.
* Workshop đã đủ số lượng nhưng vẫn nhận đăng ký.
* Workshop đã đóng vẫn cho đăng ký.
* Khó thống kê sinh viên tham gia từng workshop.
* Khó xem lịch sử workshop của từng sinh viên.
* Mất nhiều thời gian tổng hợp dữ liệu thủ công.

---

### Người dùng chính

* **Quản trị viên (Admin):**

  * Quản lý sinh viên.
  * Quản lý workshop.
  * Theo dõi danh sách đăng ký.

* **Sinh viên:**

  * Đăng ký workshop.
  * Xem các workshop đã đăng ký.
  * Hủy đăng ký.

---

### Chức năng hệ thống

* Quản lý sinh viên.
* Quản lý workshop.
* Đăng ký workshop.
* Hủy đăng ký.
* Xem danh sách workshop của sinh viên.
* Xem danh sách sinh viên của workshop.
* Kiểm tra điều kiện đăng ký.

---

### Chức năng quan trọng nhất

**Đăng ký workshop (Registration).**

Vì API này liên quan đến nhiều quy tắc nghiệp vụ:

* Student tồn tại.
* Workshop tồn tại.
* Workshop mở đăng ký.
* Workshop chưa đủ chỗ.
* Không đăng ký trùng.
* Student đang hoạt động.

---

# 7.2. Thiết kế cơ sở dữ liệu

## Student

| Field        | Type                   |
| ------------ | ---------------------- |
| id           | INT PK                 |
| student_code | VARCHAR UNIQUE         |
| full_name    | VARCHAR                |
| email        | VARCHAR UNIQUE         |
| status       | ENUM(ACTIVE, INACTIVE) |

---

## Workshop

| Field                | Type                          |
| -------------------- | ----------------------------- |
| id                   | INT PK                        |
| title                | VARCHAR                       |
| description          | TEXT                          |
| maximum_participants | INT                           |
| start_time           | DATETIME                      |
| status               | ENUM(OPEN, CLOSED, CANCELLED) |

---

## Registration

| Field         | Type                        |
| ------------- | --------------------------- |
| id            | INT PK                      |
| student_id    | INT FK                      |
| workshop_id   | INT FK                      |
| registered_at | DATETIME                    |
| status        | ENUM(REGISTERED, CANCELLED) |

---

## Quan hệ

```
Student
    │1
    │
    │
    N
Registration
    N
    │
    │1
Workshop
```

Quan hệ:

* Student 1-N Registration
* Workshop 1-N Registration
* Student N-N Workshop

---

# Kiến trúc Project

```
app/
│
├── main.py
│
├── database.py
│
├── models.py
│
├── schemas.py
│
├── dependencies.py
│
├── routers/
│      ├── students.py
│      ├── workshops.py
│      └── registrations.py
│
├── services/
│      ├── student_service.py
│      ├── workshop_service.py
│      └── registration_service.py
│
└── utils/
```

---

# Các quyết định thiết kế

## Workshop Status

```
OPEN
CLOSED
CANCELLED
```

Ý nghĩa

OPEN

> Có thể đăng ký

CLOSED

> Hết thời gian đăng ký

CANCELLED

> Workshop bị hủy

---

## Student Status

```
ACTIVE

INACTIVE
```

INACTIVE

→ Không được đăng ký.

---

## Khi hủy đăng ký

**Không xóa dữ liệu.**

Đổi trạng thái

```
REGISTERED

↓

CANCELLED
```

Lý do

* Giữ lịch sử.
* Dễ thống kê.

---

## Workshop đã bắt đầu

Không cho đăng ký.

Điều kiện

```
current_time >= start_time
```

↓

400 Bad Request

---

## Workshop bị hủy

Tất cả Registration

↓

CANCELLED

---

## Email và Student Code

Đều phải UNIQUE.

---

## Response

Trả dữ liệu dạng lồng nhau.

Ví dụ

```json
{
  "id":1,
  "title":"FastAPI",

  "students":[
      ...
  ]
}
```

Dễ dùng hơn phía Frontend.

---

# API

## Student

| Method | Endpoint       |
| ------ | -------------- |
| POST   | /students      |
| GET    | /students      |
| GET    | /students/{id} |
| PUT    | /students/{id} |
| DELETE | /students/{id} |

---

## Workshop

| Method | Endpoint        |
| ------ | --------------- |
| POST   | /workshops      |
| GET    | /workshops      |
| GET    | /workshops/{id} |
| PUT    | /workshops/{id} |
| DELETE | /workshops/{id} |

---

## Registration

| Method | Endpoint                 |
| ------ | ------------------------ |
| POST   | /registrations           |
| PUT    | /registrations/{id}      |
| GET    | /students/{id}/workshops |
| GET    | /workshops/{id}/students |

---

# Luồng đăng ký Workshop

```
Client
    │
    ▼
POST /registrations
    │
    ▼
Student tồn tại?
    │
    ├── Không → 404
    │
    ▼
Workshop tồn tại?
    │
    ├── Không → 404
    │
    ▼
Student ACTIVE?
    │
    ├── Không → 400
    │
    ▼
Workshop OPEN?
    │
    ├── Không → 400
    │
    ▼
Workshop đã bắt đầu?
    │
    ├── Có → 400
    │
    ▼
Đăng ký trùng?
    │
    ├── Có → 409
    │
    ▼
Workshop đủ người?
    │
    ├── Có → 400
    │
    ▼
Tạo Registration
    │
    ▼
201 Created
```

---

# Các Service nên tách

### Student Service

* create_student()
* get_students()
* get_student()

---

### Workshop Service

* create_workshop()
* get_workshops()
* get_workshop()

---

### Registration Service

* register_workshop()
* cancel_registration()
* get_student_workshops()
* get_workshop_students()

---

# Các quy tắc nghiệp vụ

| Quy tắc                   | HTTP |
| ------------------------- | ---- |
| Student không tồn tại     | 404  |
| Workshop không tồn tại    | 404  |
| Student INACTIVE          | 400  |
| Workshop CLOSED           | 400  |
| Workshop CANCELLED        | 400  |
| Workshop đã bắt đầu       | 400  |
| Workshop đủ người         | 400  |
| Đăng ký trùng             | 409  |
| Hủy đăng ký không tồn tại | 404  |

---

# Kết luận

Hệ thống được thiết kế theo mô hình **3 bảng (`Student` - `Workshop` - `Registration`) với quan hệ N-N thông qua bảng trung gian `Registration`**, tuân thủ kiến trúc FastAPI tách **router → service → model/schema**. Việc **không xóa bản ghi khi hủy đăng ký mà chỉ cập nhật trạng thái** giúp bảo toàn lịch sử và hỗ trợ thống kê. Các quy tắc nghiệp vụ (kiểm tra tồn tại, trạng thái, giới hạn số lượng, chống đăng ký trùng) đều được xử lý tại tầng service, giúp mã nguồn dễ bảo trì, mở rộng và phù hợp với các hệ thống quản lý thực tế.
