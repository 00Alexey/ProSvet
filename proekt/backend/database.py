from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Хранилище базы рядом с корнем проекта (чтобы файл всегда в одном месте)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "notebook.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
