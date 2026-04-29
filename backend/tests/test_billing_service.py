import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock
from backend.models.billing import TenantQuota
from backend.models.workspace import Workspace
from backend.services.billing_service import BillingService

def test_verify_quota_creates_default(monkeypatch):
    mock_db = MagicMock()
    
    # Simulate finding no existing quota
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Need to mock db.refresh to assign defaults to the new quota
    def mock_refresh(obj):
        obj.monthly_budget_hard_limit = 100.0
        obj.monthly_budget_soft_limit = 50.0
        obj.is_blocked = False
        
    mock_db.refresh.side_effect = mock_refresh
    monkeypatch.setattr(BillingService, "calculate_current_spend", lambda db, ws_id: 0.0)
    
    quota = BillingService.verify_quota(mock_db, workspace_id=1)
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_verify_quota_blocked():
    mock_db = MagicMock()
    mock_quota = TenantQuota(workspace_id=1, is_blocked=True)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_quota
    
    with pytest.raises(HTTPException) as exc_info:
        BillingService.verify_quota(mock_db, workspace_id=1)
        
    assert exc_info.value.status_code == 402
    assert "administratively blocked" in exc_info.value.detail

def test_verify_quota_hard_limit_exceeded(monkeypatch):
    mock_db = MagicMock()
    mock_quota = TenantQuota(
        workspace_id=1, 
        monthly_budget_hard_limit=10.0,
        is_blocked=False
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_quota
    
    # Mock calculate_current_spend to return $15.00
    monkeypatch.setattr(BillingService, "calculate_current_spend", lambda db, ws_id: 15.0)
    
    with pytest.raises(HTTPException) as exc_info:
        BillingService.verify_quota(mock_db, workspace_id=1)
        
    assert exc_info.value.status_code == 402
    assert "API quota exceeded" in exc_info.value.detail
    mock_db.add.assert_called_once() # Audit Log added

def test_verify_quota_soft_limit_only(monkeypatch):
    mock_db = MagicMock()
    mock_quota = TenantQuota(
        workspace_id=1, 
        monthly_budget_soft_limit=5.0,
        monthly_budget_hard_limit=10.0,
        is_blocked=False
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_quota
    
    # Mock spend to $7.00
    monkeypatch.setattr(BillingService, "calculate_current_spend", lambda db, ws_id: 7.0)
    
    returned_quota = BillingService.verify_quota(mock_db, workspace_id=1)
    assert returned_quota.workspace_id == 1
