import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status

class SlidingWindowRateLimiter:
    """
    In-memory Sliding Window Rate Limiter.
    In multi-instance production environments, this can seamlessly be backed
    by a Redis Sorted Set (ZADD, ZREMRANGEBYSCORE, ZCARD) using the same interface.
    """
    def __init__(self, requests_limit: int = 5, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.history: Dict[str, List[float]] = defaultdict(list)

    def check(self, key: str):
        now = time.time()
        window_start = now - self.window_seconds
        
        # Prune expired request timestamps
        self.history[key] = [t for t in self.history[key] if t > window_start]
        
        if len(self.history[key]) >= self.requests_limit:
            oldest_request = self.history[key][0]
            retry_after = int(oldest_request + self.window_seconds - now)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: max {self.requests_limit} requests per {self.window_seconds}s. Try again in {max(1, retry_after)}s.",
                headers={"Retry-After": str(max(1, retry_after))}
            )
        
        self.history[key].append(now)

# Pre-configured rate limiter instances for dependency injection
inquiry_rate_limiter = SlidingWindowRateLimiter(requests_limit=5, window_seconds=60)
application_rate_limiter = SlidingWindowRateLimiter(requests_limit=3, window_seconds=60)
auth_rate_limiter = SlidingWindowRateLimiter(requests_limit=5, window_seconds=60)
payment_rate_limiter = SlidingWindowRateLimiter(requests_limit=10, window_seconds=60)

def rate_limit_dependency(limiter: SlidingWindowRateLimiter):
    """Factory dependency injecting rate limit enforcement on specific FastAPI routes."""
    async def dependency(request: Request):
        # Extract client IP respecting standard reverse-proxy headers
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
        key = f"{client_ip}:{request.url.path}"
        limiter.check(key)
    return dependency
