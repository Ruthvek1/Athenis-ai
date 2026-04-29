from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base

class TenantQuota(Base):
    __tablename__ = "tenant_quotas"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Pricing configuration (Cost per 1k tokens)
    cost_per_1k_prompt = Column(Float, default=0.01)
    cost_per_1k_completion = Column(Float, default=0.03)
    
    # Limits
    monthly_budget_soft_limit = Column(Float, default=50.0)  # Trigger warning
    monthly_budget_hard_limit = Column(Float, default=100.0) # Block further requests
    
    # State
    is_blocked = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    workspace = relationship("Workspace")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    action = Column(String, nullable=False) # e.g. "QUOTA_EXCEEDED", "QUOTA_UPDATED"
    details = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
