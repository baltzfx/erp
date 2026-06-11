from itsdangerous import URLSafeSerializer
from app.core.config import settings

serializer = URLSafeSerializer(settings.SECRET_KEY)

def create_session_token(user_id: int) -> str:
    """Create a signed token for the user ID."""
    return serializer.dumps({"user_id": user_id})

def get_user_id_from_token(token: str) -> int | None:
    """Extract user ID from a signed token."""
    try:
        data = serializer.loads(token)
        return data.get("user_id")
    except Exception:
        return None
