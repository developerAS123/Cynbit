import pytest
from implementation.middleware.rate_limit import SlidingWindowRateLimiter

def test_sliding_window_rate_limiter_blocks_excess_calls():
    """Unit test validating rate limiter threshold enforcement and HTTP 429 exception."""
    limiter = SlidingWindowRateLimiter(requests_limit=3, window_seconds=10)
    test_key = "192.168.1.100:/api/v1/inquiries"
    
    # 3 allowed calls
    limiter.check(test_key)
    limiter.check(test_key)
    limiter.check(test_key)
    
    # 4th call must raise HTTPException 429
    with pytest.raises(Exception) as exc_info:
        limiter.check(test_key)
        
    assert "429" in str(exc_info.value)
    assert "Rate limit exceeded" in str(exc_info.value)

