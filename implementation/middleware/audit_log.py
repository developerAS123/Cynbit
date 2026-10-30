import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("cynbit.audit")
logging.basicConfig(level=logging.INFO)

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured request timing and security audit logger.
    Emits structured log entries capturing response latency and caller IP.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.info(
                f"AUDIT: method={request.method} path={request.url.path} "
                f"status={response.status_code} ip={client_ip} duration={duration_ms:.2f}ms"
            )
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"AUDIT_ERROR: method={request.method} path={request.url.path} "
                f"ip={client_ip} duration={duration_ms:.2f}ms error={str(exc)}"
            )
            raise exc
