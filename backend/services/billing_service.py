from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
import structlog
from backend.models.metrics import TokenUsage
from backend.models.billing import TenantQuota, AuditLog
from backend.models.workspace import Workspace
from datetime import datetime, date
import calendar

logger = structlog.get_logger(__name__)

class BillingService:
    @staticmethod
    def get_current_month_bounds():
        now = datetime.utcnow()
        start = datetime(now.year, now.month, 1)
        last_day = calendar.monthrange(now.year, now.month)[1]
        end = datetime(now.year, now.month, last_day, 23, 59, 59, 999999)
        return start, end

    @staticmethod
    def calculate_current_spend(db: Session, workspace_id: int) -> float:
        """
        Calculates the exact monetary spend for a workspace in the current billing cycle.
        """
        start, end = BillingService.get_current_month_bounds()
        
        quota = db.query(TenantQuota).filter(TenantQuota.workspace_id == workspace_id).first()
        if not quota:
            return 0.0
            
        usage_records = db.query(TokenUsage).join(
            Workspace, Workspace.id == workspace_id
        ).filter(
            TokenUsage.created_at >= start,
            TokenUsage.created_at <= end
        ).all()
        
        # Token usage is currently linked to user or session. 
        # In a real app we'd map TokenUsage -> Session -> Workspace. 
        # For MVP we will just aggregate all usage that belongs to users in this workspace.
        # Let's assume we update TokenUsage to include workspace_id or we map it via session.
        # Since TokenUsage has session_id, we can map: TokenUsage -> ChatSession -> Workspace
        from backend.models.chat import ChatSession
        
        total_prompt = db.query(func.sum(TokenUsage.prompt_tokens)).join(
            ChatSession, TokenUsage.session_id == ChatSession.id
        ).filter(
            ChatSession.workspace_id == workspace_id,
            TokenUsage.created_at >= start,
            TokenUsage.created_at <= end
        ).scalar() or 0
        
        total_completion = db.query(func.sum(TokenUsage.completion_tokens)).join(
            ChatSession, TokenUsage.session_id == ChatSession.id
        ).filter(
            ChatSession.workspace_id == workspace_id,
            TokenUsage.created_at >= start,
            TokenUsage.created_at <= end
        ).scalar() or 0
        
        cost = (total_prompt / 1000.0) * quota.cost_per_1k_prompt + \
               (total_completion / 1000.0) * quota.cost_per_1k_completion
               
        return round(cost, 4)

    @staticmethod
    def verify_quota(db: Session, workspace_id: int):
        """
        Verifies if a workspace has exceeded its budget.
        Raises HTTP 402 if hard limit is exceeded.
        """
        quota = db.query(TenantQuota).filter(TenantQuota.workspace_id == workspace_id).first()
        if not quota:
            # Create default quota if none exists
            quota = TenantQuota(workspace_id=workspace_id)
            db.add(quota)
            db.commit()
            db.refresh(quota)
            
        if quota.is_blocked:
            raise HTTPException(status_code=402, detail="Workspace is administratively blocked.")
            
        spend = BillingService.calculate_current_spend(db, workspace_id)
        
        if spend >= quota.monthly_budget_hard_limit:
            if not quota.is_blocked:
                # Log the limit break
                log = AuditLog(
                    workspace_id=workspace_id,
                    action="QUOTA_EXCEEDED",
                    details=f"Hard limit of ${quota.monthly_budget_hard_limit} exceeded. Spend: ${spend}"
                )
                db.add(log)
                db.commit()
            raise HTTPException(status_code=402, detail=f"Monthly API quota exceeded (${spend}/${quota.monthly_budget_hard_limit}). Please upgrade your plan.")
            
        if spend >= quota.monthly_budget_soft_limit:
            # We don't block here, but we might log a warning
            logger.warning(f"Workspace {workspace_id} approaching budget limit.", spend=spend, limit=quota.monthly_budget_hard_limit)
            
        return quota
