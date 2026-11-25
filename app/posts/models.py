from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, Enum, Boolean, true
from sqlalchemy.orm import Mapped, mapped_column

from app import db

CATEGORIES = ("news", "publication", "tech", "other")


def utcnow():
    # datetime.utcnow() застарів у Python 3.12+, тому беремо UTC-час без tzinfo
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Post(db.Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    posted: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    category: Mapped[str] = mapped_column(
        Enum(*CATEGORIES, name="post_category"), default="other"
    )
    # server_default потрібен, щоб міграція заповнила значення для вже існуючих рядків
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    author: Mapped[str] = mapped_column(String(20), default="Anonymous", server_default="Anonymous")

    def __repr__(self):
        return f"<Post(title={self.title})>"
