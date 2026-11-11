import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db import Base


class ProspectStatus(str, enum.Enum):
    FOUND = "found"
    EVALUATING = "evaluating"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"
    RESPONDED = "responded"
    BLACKLISTED = "blacklisted"


class DraftStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    FAILED = "failed"


class MessageStatus(str, enum.Enum):
    SENT = "sent"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    segment_description = Column(Text, nullable=True)
    max_sends_per_run = Column(Integer, default=25)
    max_sends_per_day = Column(Integer, default=100)
    cooldown_seconds = Column(Integer, default=90)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)

    seed_accounts = relationship("SeedAccount", back_populates="campaign")
    prospects = relationship("Prospect", back_populates="campaign")
    drafts = relationship("Draft", back_populates="campaign")
    messages_sent = relationship("MessageSent", back_populates="campaign")
    interactions = relationship("Interaction", back_populates="campaign")


class SeedAccount(Base):
    __tablename__ = "seed_accounts"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    username = Column(String, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    source = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="seed_accounts")


class Prospect(Base):
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    x_user_id = Column(String, nullable=True, index=True)
    username = Column(String, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    location = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    source_seed_username = Column(String, nullable=True)
    fit_score = Column(Integer, default=0)
    fit_reason = Column(Text, nullable=True)
    status = Column(Enum(ProspectStatus), default=ProspectStatus.FOUND)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="prospects")
    evidence = relationship("Evidence", back_populates="prospect", uselist=False)
    drafts = relationship("Draft", back_populates="prospect")
    messages_sent = relationship("MessageSent", back_populates="prospect")
    interactions = relationship("Interaction", back_populates="prospect")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), unique=True)
    bio_text = Column(Text, nullable=True)
    recent_posts_json = Column(Text, nullable=True)
    evidence_summary = Column(Text, nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)

    prospect = relationship("Prospect", back_populates="evidence")


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    dm_text = Column(Text, nullable=False)
    evidence_used = Column(Text, nullable=True)
    status = Column(Enum(DraftStatus), default=DraftStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)

    prospect = relationship("Prospect", back_populates="drafts")
    campaign = relationship("Campaign", back_populates="drafts")


class MessageSent(Base):
    __tablename__ = "messages_sent"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    dm_text = Column(Text, nullable=False)
    x_dm_id = Column(String, nullable=True, index=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT)
    error = Column(Text, nullable=True)

    prospect = relationship("Prospect", back_populates="messages_sent")
    campaign = relationship("Campaign", back_populates="messages_sent")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    type = Column(String, nullable=False)  # sent / replied / opened / clicked
    direction = Column(String, nullable=False)  # inbound / outbound
    content_snippet = Column(Text, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    needs_attention = Column(Boolean, default=False)

    prospect = relationship("Prospect", back_populates="interactions")
    campaign = relationship("Campaign", back_populates="interactions")


class RateLimitState(Base):
    __tablename__ = "rate_limit_state"

    endpoint = Column(String, primary_key=True)
    remaining = Column(Integer, nullable=True)
    reset_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
