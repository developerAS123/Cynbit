from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects enterprise defense-in-depth security headers onto every HTTP response,
    neutralizing Clickjacking, MIME sniffing, and cross-site framing attacks.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Clickjacking Prevention
        response.headers["X-Frame-Options"] = "DENY"
        
        # MIME-Confusion Mitigation
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Referrer Token Leaks Mitigation
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Hardware Sensor Restriction
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        
        # Transport Layer Strict Enforcement
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        
        # Restrictive Content Security Policy (Allows Cashfree SDK modal frames)
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://sdk.cashfree.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "frame-src https://sdk.cashfree.com; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response

