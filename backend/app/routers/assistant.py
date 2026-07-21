from fastapi import APIRouter

from app.services.ai_service import build_assistant_response

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/explain")
def explain(payload: dict[str, str]) -> dict[str, object]:
    prompt = payload.get("prompt", "Explain this alert")
    return build_assistant_response(prompt, {"context": payload})
