from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False}
    if db_url.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401  (ensure models registered)
    Base.metadata.create_all(bind=engine)

    # Auto-migrate new columns if table already exists in SQLite/Postgres
    with engine.connect() as conn:
        for col, col_type in [
            ("x_user_id", "VARCHAR"),
            ("profile_image_url", "VARCHAR"),
            ("location", "VARCHAR"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE prospects ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass
