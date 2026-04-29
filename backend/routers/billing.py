from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.core.database import get_db
from backend.core.deps import get_current_active_user
from backend.models.user import User
from backend.models.billing import TenantQuota, AuditLog
from backend.models.workspace import Workspace
from backend.services.billing_service import BillingService

router = APIRouter()

class QuotaResponse(BaseModel):
    workspace_id: int
    cost_per_1k_prompt: float
    cost_per_1k_completion: float
    monthly_budget_soft_limit: float
    monthly_budget_hard_limit: float
    is_blocked: bool
    current_spend: float

class QuotaUpdateRequest(BaseModel):
    cost_per_1k_prompt: Optional[float] = None
    cost_per_1k_completion: Optional[float] = None
    monthly_budget_soft_limit: Optional[float] = None
    monthly_budget_hard_limit: Optional[float] = None
    is_blocked: Optional[bool] = None

@router.get("/workspaces/{workspace_id}/quota", response_model=QuotaResponse)
def get_workspace_quota(
    workspace_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    quota = db.query(TenantQuota).filter(TenantQuota.workspace_id == workspace_id).first()
    if not quota:
        quota = TenantQuota(workspace_id=workspace_id)
        db.add(quota)
        db.commit()
        db.refresh(quota)
        
    spend = BillingService.calculate_current_spend(db, workspace_id)
    
    return QuotaResponse(
        workspace_id=quota.workspace_id,
        cost_per_1k_prompt=quota.cost_per_1k_prompt,
        cost_per_1k_completion=quota.cost_per_1k_completion,
        monthly_budget_soft_limit=quota.monthly_budget_soft_limit,
        monthly_budget_hard_limit=quota.monthly_budget_hard_limit,
        is_blocked=quota.is_blocked,
        current_spend=spend
    )

@router.put("/workspaces/{workspace_id}/quota", response_model=QuotaResponse)
def update_workspace_quota(
    workspace_id: int,
    request: QuotaUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    quota = db.query(TenantQuota).filter(TenantQuota.workspace_id == workspace_id).first()
    if not quota:
        quota = TenantQuota(workspace_id=workspace_id)
        db.add(quota)
        
    old_hard_limit = quota.monthly_budget_hard_limit
    
    if request.cost_per_1k_prompt is not None:
        quota.cost_per_1k_prompt = request.cost_per_1k_prompt
    if request.cost_per_1k_completion is not None:
        quota.cost_per_1k_completion = request.cost_per_1k_completion
    if request.monthly_budget_soft_limit is not None:
        quota.monthly_budget_soft_limit = request.monthly_budget_soft_limit
    if request.monthly_budget_hard_limit is not None:
        quota.monthly_budget_hard_limit = request.monthly_budget_hard_limit
    if request.is_blocked is not None:
        quota.is_blocked = request.is_blocked
        
    db.commit()
    db.refresh(quota)
    
    # Audit Log
    log = AuditLog(
        workspace_id=workspace_id,
        user_id=current_user.id,
        action="QUOTA_UPDATED",
        details=f"Quota updated. New Hard Limit: {quota.monthly_budget_hard_limit}. Old Hard Limit: {old_hard_limit}."
    )
    db.add(log)
    db.commit()
    
    spend = BillingService.calculate_current_spend(db, workspace_id)
    return QuotaResponse(
        workspace_id=quota.workspace_id,
        cost_per_1k_prompt=quota.cost_per_1k_prompt,
        cost_per_1k_completion=quota.cost_per_1k_completion,
        monthly_budget_soft_limit=quota.monthly_budget_soft_limit,
        monthly_budget_hard_limit=quota.monthly_budget_hard_limit,
        is_blocked=quota.is_blocked,
        current_spend=spend
    )
