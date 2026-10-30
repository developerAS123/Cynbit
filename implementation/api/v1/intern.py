from fastapi import APIRouter, Depends, status
from implementation.api.v1.auth import get_current_user
from implementation.models.entities import User

router = APIRouter(prefix="/intern", tags=["Intern Portal"])

@router.get("/dashboard", status_code=status.HTTP_200_OK)
async def get_intern_dashboard(user: User = Depends(get_current_user)):
    """
    Authenticated Intern Learning Dashboard.
    PROTECTION: Unlike the Next.js static prerender leak, this endpoint enforces
    strict server-side JWT authentication, preventing unauthorized access to proprietary
    coursework, challenge specs, and internal engineering materials.
    """
    return {
        "status": "authorized",
        "intern": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role
        },
        "curriculum": {
            "track": "Backend Engineering",
            "active_sprint": "Sprint 1: Architecture & API Hardening",
            "modules": [
                {
                    "module_id": "MOD-01",
                    "title": "FastAPI Core & Pydantic Validation",
                    "status": "IN_PROGRESS"
                },
                {
                    "module_id": "MOD-02",
                    "title": "Asynchronous SQLAlchemy & Database Migrations",
                    "status": "UPCOMING"
                },
                {
                    "module_id": "MOD-03",
                    "title": "Zero-Trust Payment Reconciliation & HMAC Webhooks",
                    "status": "UPCOMING"
                }
            ]
        }
    }

@router.get("/tasks", status_code=status.HTTP_200_OK)
async def get_intern_tasks(user: User = Depends(get_current_user)):
    """Returns assigned engineering deliverables for the active sprint."""
    return {
        "tasks": [
            {
                "id": "TASK-101",
                "title": "Implement Sliding Window Rate Limiter",
                "deliverable": "Pull request with unit tests and latency benchmarks"
            },
            {
                "id": "TASK-102",
                "title": "Verify Cashfree HMAC-SHA256 Webhooks",
                "deliverable": "Webhook endpoint with timing-safe signature comparison"
            }
        ]
    }
