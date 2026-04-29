from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import get_db
from backend.core.deps import get_current_active_user
from backend.models.user import User
from backend.models.chat import ChatMessage, ChatSession, MessageFeedback
from unittest.mock import MagicMock

client = TestClient(app)

def test_submit_feedback_mock():
    # Mock User
    mock_user = User(id=1, email="testuser@example.com")
    
    # Mock DB Session
    mock_db = MagicMock()
    
    # Mock message
    mock_msg = ChatMessage(id=1, session_id=1, role="assistant")
    mock_session = ChatSession(id=1, user_id=1)
    
    # Setup mock query chain
    # msg query
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_msg, # message query
        mock_session, # session query
        None # feedback query (None means not found, will create new)
    ]
    
    # Override dependencies
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    
    response = client.post(
        "/api/v1/chat/messages/1/feedback",
        json={"is_positive": 1, "comments": "Great!"}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Feedback submitted successfully"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    
    # Reset overrides
    app.dependency_overrides.clear()
