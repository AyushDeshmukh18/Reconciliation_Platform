from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class RuleConfig(Base):
    __tablename__ = "rule_configs"

    rule_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    gap_type: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    conditions: Mapped[dict] = mapped_column(nullable=False)
    confidence_base: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
