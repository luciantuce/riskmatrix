from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    End-user account, mirror of the Clerk identity.
    Created via Clerk webhook `user.created`; lazy-created from JWT claims
    if a request arrives before the webhook is processed.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clerk_user_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    role = Column(String, default="client", nullable=False)  # 'client' | 'admin' | 'super_admin'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    clients = relationship("Client", back_populates="user")
    kit_submissions = relationship("KitSubmission", back_populates="user")
    kit_results = relationship("KitResult", back_populates="user")


class WebhookEvent(Base):
    """
    Idempotency log for inbound webhook events from Clerk and Stripe.
    Each event is identified by (source, external_id); duplicates short-circuit.
    """
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)        # 'clerk' | 'stripe'
    external_id = Column(String, nullable=False)   # 'evt_xxx'
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_webhook_events_source_external"),
        Index("idx_webhook_events_source_received", "source", "received_at"),
    )


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True, index=True)

    user = relationship("User", back_populates="clients")
    profile = relationship("ClientProfile", back_populates="client", uselist=False, cascade="all, delete-orphan")
    kit_submissions = relationship("KitSubmission", back_populates="client", cascade="all, delete-orphan")
    kit_results = relationship("KitResult", back_populates="client", cascade="all, delete-orphan")


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, unique=True)
    version = Column(Integer, default=1, nullable=False)
    status = Column(String, default="draft", nullable=False)
    answers_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    client = relationship("Client", back_populates="profile")


class Kit(Base):
    __tablename__ = "kits"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    documentation_url = Column(String, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    pricing_type = Column(String, default="one_time", nullable=False)
    price_eur = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    versions = relationship("KitVersion", back_populates="kit", cascade="all, delete-orphan")


class KitVersion(Base):
    __tablename__ = "kit_versions"

    id = Column(Integer, primary_key=True, index=True)
    kit_id = Column(Integer, ForeignKey("kits.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    status = Column(String, default="published", nullable=False)
    notes = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    kit = relationship("Kit", back_populates="versions")
    sections = relationship("KitSection", back_populates="kit_version", cascade="all, delete-orphan")
    rules = relationship("KitRule", back_populates="kit_version", cascade="all, delete-orphan")
    templates = relationship("KitDocumentTemplate", back_populates="kit_version", cascade="all, delete-orphan")
    submissions = relationship("KitSubmission", back_populates="kit_version")
    results = relationship("KitResult", back_populates="kit_version")


class KitSection(Base):
    __tablename__ = "kit_sections"

    id = Column(Integer, primary_key=True, index=True)
    kit_version_id = Column(Integer, ForeignKey("kit_versions.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)

    kit_version = relationship("KitVersion", back_populates="sections")
    questions = relationship("KitQuestion", back_populates="section", cascade="all, delete-orphan")


class Risk(Base):
    """Biblioteca celor 50 riscuri structurale (R1-R50)."""
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    category = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    impact_default = Column(Integer, default=2, nullable=False)
    probability_default = Column(Integer, default=2, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)

    question_maps = relationship("QuestionRiskMap", back_populates="risk", cascade="all, delete-orphan")


class QuestionRiskMap(Base):
    """Mapare întrebare → risc: când răspunsul e DA sau NU, se activează riscul."""
    __tablename__ = "question_risk_maps"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("kit_questions.id"), nullable=False)
    risk_id = Column(Integer, ForeignKey("risks.id"), nullable=False)
    trigger_on_true = Column(Boolean, nullable=False)
    probability_override = Column(Integer, nullable=True)
    impact_override = Column(Integer, nullable=True)

    question = relationship("KitQuestion", back_populates="risk_maps")
    risk = relationship("Risk", back_populates="question_maps")


class KitQuestion(Base):
    __tablename__ = "kit_questions"

    id = Column(Integer, primary_key=True, index=True)
    kit_section_id = Column(Integer, ForeignKey("kit_sections.id"), nullable=False)
    question_key = Column(String, nullable=False)
    label = Column(String, nullable=False)
    help_text = Column(Text, nullable=True)
    question_type = Column(String, nullable=False)
    required = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    visibility_rule_json = Column(JSON, nullable=True)
    default_value_json = Column(JSON, nullable=True)
    responsabil_options_json = Column(JSON, nullable=True)

    section = relationship("KitSection", back_populates="questions")
    options = relationship("KitQuestionOption", back_populates="question", cascade="all, delete-orphan")
    risk_maps = relationship("QuestionRiskMap", back_populates="question", cascade="all, delete-orphan")


class KitQuestionOption(Base):
    __tablename__ = "kit_question_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("kit_questions.id"), nullable=False)
    value = Column(String, nullable=False)
    label = Column(String, nullable=False)
    score_hint = Column(Float, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)

    question = relationship("KitQuestion", back_populates="options")


class KitRule(Base):
    __tablename__ = "kit_rules"

    id = Column(Integer, primary_key=True, index=True)
    kit_version_id = Column(Integer, ForeignKey("kit_versions.id"), nullable=False)
    rule_code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=100, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    conditions_json = Column(JSON, default=dict, nullable=False)
    effects_json = Column(JSON, default=dict, nullable=False)

    kit_version = relationship("KitVersion", back_populates="rules")


class KitSubmission(Base):
    __tablename__ = "kit_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    kit_id = Column(Integer, ForeignKey("kits.id"), nullable=False)
    kit_version_id = Column(Integer, ForeignKey("kit_versions.id"), nullable=False)
    status = Column(String, default="draft", nullable=False)
    answers_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="kit_submissions")
    client = relationship("Client", back_populates="kit_submissions")
    kit_version = relationship("KitVersion", back_populates="submissions")


class KitResult(Base):
    __tablename__ = "kit_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    kit_id = Column(Integer, ForeignKey("kits.id"), nullable=False)
    kit_version_id = Column(Integer, ForeignKey("kit_versions.id"), nullable=False)
    submission_id = Column(Integer, ForeignKey("kit_submissions.id"), nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)
    risk_level = Column(String, default="LOW", nullable=False)
    risk_flags_json = Column(JSON, default=list, nullable=False)
    responsibility_matrix_json = Column(JSON, default=list, nullable=False)
    engagement_level = Column(String, default="standard", nullable=False)
    tariff_adjustment_pct = Column(Float, default=0.0, nullable=False)
    active_risks_json = Column(JSON, default=list, nullable=False)
    result_json = Column(JSON, default=dict, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="kit_results")
    client = relationship("Client", back_populates="kit_results")
    kit_version = relationship("KitVersion", back_populates="results")


class KitDocumentTemplate(Base):
    __tablename__ = "kit_document_templates"

    id = Column(Integer, primary_key=True, index=True)
    kit_version_id = Column(Integer, ForeignKey("kit_versions.id"), nullable=False)
    document_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    intro_text = Column(Text, nullable=True)
    footer_text = Column(Text, nullable=True)
    signature_block_text = Column(Text, nullable=True)
    show_risk_score = Column(Boolean, default=True, nullable=False)
    show_risk_flags = Column(Boolean, default=True, nullable=False)
    show_responsibility_matrix = Column(Boolean, default=True, nullable=False)
    show_tariff_recommendation = Column(Boolean, default=False, nullable=False)
    template_json = Column(JSON, default=dict, nullable=False)

    kit_version = relationship("KitVersion", back_populates="templates")
