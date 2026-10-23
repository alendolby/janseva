import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, CheckConstraint, JSON
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.core.db import Base

def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
def uid():
    return str(uuid.uuid4())
def pk():
    return Column(String(36), primary_key=True, default=uid)
def stamp():
    return Column(DateTime, nullable=False, default=now)

class Role(Base):
    __tablename__ = "roles"
    name = Column(String(16), primary_key=True)
class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role_name = Column(String(16), ForeignKey("roles.name"), primary_key=True)
    __table_args__ = (UniqueConstraint("user_id"),)
class Department(Base):
    __tablename__ = "departments"
    id = pk(); name = Column(String(120), nullable=False, unique=True)
class District(Base):
    __tablename__ = "districts"
    id = pk(); name = Column(String(120), nullable=False, unique=True)
class LocalBody(Base):
    __tablename__ = "local_bodies"
    id = pk(); name = Column(String(120), nullable=False)
    district_id = Column(String(36), ForeignKey("districts.id"), nullable=False)
class Ward(Base):
    __tablename__ = "wards"
    id = pk(); name = Column(String(120), nullable=False)
    local_body_id = Column(String(36), ForeignKey("local_bodies.id"), nullable=False)
    boundary = Column(Text, nullable=False)  # GeoJSON import source for portable test mode
    geometry = Column(Text().with_variant(Geometry("MULTIPOLYGON", srid=4326), "postgresql"))
    source = Column(String(255), nullable=False)
    verified = Column(Boolean, nullable=False, default=False)
class Office(Base):
    __tablename__ = "offices"
    id = pk(); name = Column(String(120), nullable=False, unique=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False)
    local_body_id = Column(String(36), ForeignKey("local_bodies.id"), nullable=False)
    parent_office_id = Column(String(36), ForeignKey("offices.id"))
class User(Base):
    __tablename__ = "users"
    id = pk(); email = Column(String(254), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    verified = Column(Boolean, nullable=False, default=False)
    session_version = Column(Integer, nullable=False, default=0)
    created_at = stamp()
    roles = relationship("UserRole", cascade="all, delete-orphan", lazy="selectin")
    office_membership = relationship("OfficeUser", uselist=False, lazy="selectin")
    @property
    def role(self):
        return self.roles[0].role_name if self.roles else "CITIZEN"
    @property
    def office_id(self):
        return self.office_membership.office_id if self.office_membership else None
class CitizenProfile(Base):
    __tablename__ = "citizen_profiles"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    preferred_language = Column(String(20), default="en", nullable=False)
class OfficeUser(Base):
    __tablename__ = "office_users"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    office_id = Column(String(36), ForeignKey("offices.id"), nullable=False, index=True)
class AuthToken(Base):
    __tablename__ = "auth_tokens"
    id = pk(); user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    digest = Column(String(64), unique=True, nullable=False)
    purpose = Column(String(16), nullable=False); expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, nullable=False, default=False)
class Category(Base):
    __tablename__ = "categories"
    id = pk(); name = Column(String(100), unique=True, nullable=False)
class RoutingRule(Base):
    __tablename__ = "routing_rules"
    id = pk(); category_id = Column(String(36), ForeignKey("categories.id"), nullable=False)
    ward_id = Column(String(36), ForeignKey("wards.id"), nullable=False)
    office_id = Column(String(36), ForeignKey("offices.id"), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    source = Column(String(255), nullable=False)
    verified = Column(Boolean, nullable=False, default=False)
    __table_args__ = (UniqueConstraint("category_id", "ward_id"),)
class SlaPolicy(Base):
    __tablename__ = "sla_policies"
    id = pk(); category_id = Column(String(36), ForeignKey("categories.id"), nullable=False)
    severity = Column(String(16), nullable=False)
    hours = Column(Integer, nullable=False); warning_hours = Column(Integer, nullable=False)
    escalation_office_id = Column(String(36), ForeignKey("offices.id"))
    __table_args__ = (UniqueConstraint("category_id", "severity"), CheckConstraint("hours > 0 AND warning_hours >= 0 AND warning_hours < hours"))
class CaseCounter(Base):
    __tablename__ = "case_counters"
    year = Column(Integer, primary_key=True); value = Column(Integer, nullable=False)
class Case(Base):
    __tablename__ = "cases"
    id = pk(); public_case_id = Column(String(30), nullable=False, unique=True, index=True)
    citizen_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("categories.id"), index=True)
    title = Column(String(160), nullable=False); description = Column(Text, nullable=False)
    status = Column(String(40), nullable=False, index=True)
    priority = Column(String(16), nullable=False)
    severity_score = Column(Integer, nullable=False)
    assigned_office_id = Column(String(36), ForeignKey("offices.id"), index=True)
    assigned_officer_id = Column(String(36), ForeignKey("users.id"))
    routing_review_required = Column(Boolean, default=False, nullable=False)
    sla_deadline = Column(DateTime, index=True)
    resolution_note = Column(Text); resolved_at = Column(DateTime)
    created_at = stamp(); updated_at = stamp()
    category = relationship("Category", lazy="joined")
    office = relationship("Office", foreign_keys=[assigned_office_id], lazy="joined")
    __table_args__ = (CheckConstraint("severity_score >= 0 AND severity_score <= 100"), CheckConstraint("status IN ('DRAFT','SUBMITTED','UNDER_AI_ANALYSIS','ROUTING','ASSIGNED','ACKNOWLEDGED','IN_PROGRESS','WAITING_FOR_INFORMATION','RESOLVED','REJECTED','ESCALATED','CLOSED')"))
class CaseLocation(Base):
    __tablename__ = "case_locations"
    case_id = Column(String(36), ForeignKey("cases.id"), primary_key=True)
    latitude = Column(Float, nullable=False); longitude = Column(Float, nullable=False)
    geometry = Column(Text().with_variant(Geometry("POINT", srid=4326), "postgresql"), nullable=False)
    ward_id = Column(String(36), ForeignKey("wards.id")); address = Column(String(255), nullable=False)
    __table_args__ = (CheckConstraint("latitude >= -90 AND latitude <= 90 AND longitude >= -180 AND longitude <= 180"),)
class CaseEvidence(Base):
    __tablename__ = "case_evidence"
    id = pk(); case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False); storage_key = Column(String(255), unique=True, nullable=False)
    mime_type = Column(String(100), nullable=False); size = Column(Integer, nullable=False)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    kind = Column(String(16), nullable=False); uploaded_at = stamp()
class CaseEvent(Base):
    __tablename__ = "case_events"
    id = pk(); case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    actor_id = Column(String(36), ForeignKey("users.id"))
    action = Column(String(60), nullable=False); previous = Column(String(40)); current = Column(String(40))
    note = Column(Text, nullable=False, default=""); internal = Column(Boolean, nullable=False, default=False)
    created_at = stamp()
class CaseAssignment(Base):
    __tablename__ = "case_assignments"
    id = pk(); case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    office_id = Column(String(36), ForeignKey("offices.id"), nullable=False)
    officer_id = Column(String(36), ForeignKey("users.id")); actor_id = Column(String(36), ForeignKey("users.id"))
    created_at = stamp()
class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = pk(); name = Column(String(80), unique=True, nullable=False)
    dataset_version = Column(String(80), nullable=False); trained_at = stamp()
    metrics = Column(JSON, nullable=False)
class AiPrediction(Base):
    __tablename__ = "ai_predictions"
    id = pk(); case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    model_id = Column(String(36), ForeignKey("model_versions.id"), nullable=False)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False)
    confidence = Column(Float, nullable=False); corrected_category_id = Column(String(36), ForeignKey("categories.id"))
    corrected_by = Column(String(36), ForeignKey("users.id")); correction_reason = Column(Text)
    created_at = stamp()
class SeverityScore(Base):
    __tablename__ = "severity_scores"
    case_id = Column(String(36), ForeignKey("cases.id"), primary_key=True)
    score = Column(Integer, nullable=False); explanation = Column(JSON, nullable=False)
class IncidentCluster(Base):
    __tablename__ = "incident_clusters"
    id = pk(); created_at = stamp()
class IncidentMember(Base):
    __tablename__ = "incident_members"
    case_id = Column(String(36), ForeignKey("cases.id"), primary_key=True)
    cluster_id = Column(String(36), ForeignKey("incident_clusters.id"), nullable=False, index=True)
    similarity = Column(Float, nullable=False)
class SlaInstance(Base):
    __tablename__ = "sla_instances"
    case_id = Column(String(36), ForeignKey("cases.id"), primary_key=True)
    policy_id = Column(String(36), ForeignKey("sla_policies.id"), nullable=False)
    start_time = stamp(); deadline = Column(DateTime, nullable=False, index=True)
    warning_time = Column(DateTime, nullable=False); status = Column(String(20), nullable=False)
    completed_at = Column(DateTime)
class Escalation(Base):
    __tablename__ = "escalations"
    id = pk(); case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    from_level = Column(Integer, nullable=False); to_level = Column(Integer, nullable=False)
    authority_id = Column(String(36), ForeignKey("offices.id")); reason = Column(Text, nullable=False)
    created_at = stamp(); resolved_at = Column(DateTime)
class Notification(Base):
    __tablename__ = "notifications"
    id = pk(); user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("cases.id")); message = Column(Text, nullable=False)
    read = Column(Boolean, nullable=False, default=False); created_at = stamp()
class Feedback(Base):
    __tablename__ = "feedback"
    id = pk(); case_id = Column(String(36), ForeignKey("cases.id"), unique=True, nullable=False)
    citizen_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False); comment = Column(Text, nullable=False); created_at = stamp()
    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5"),)
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = pk(); actor_id = Column(String(36), ForeignKey("users.id")); case_id = Column(String(36), ForeignKey("cases.id"), index=True)
    action = Column(String(80), nullable=False); previous = Column(JSON); current = Column(JSON)
    reason = Column(Text, nullable=False, default=""); created_at = stamp()
