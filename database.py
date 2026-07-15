from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Chuỗi kết nối giả định tới MySQL
# Định dạng: mysql+pymysql://<user>:<password>@<host>:<port>/<database>
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/workshop_db"

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