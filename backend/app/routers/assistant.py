from fastapi import APIRouter, Depends

from app.services.ai_service import build_assistant_response
from app.core.permissions import Permission
from app.security import require_permission

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/explain")
def explain(payload: dict[str, str], _actor=Depends(require_permission(Permission.EVENTS_READ))) -> dict[str, object]:
    prompt = payload.get("prompt", "Explain this alert")
    return build_assistant_response(prompt, {"context": payload})
