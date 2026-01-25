"""
FastAPI dependencies for the API layer.
"""
from fastapi import Request


def get_rate_limiter(request: Request):
    """
    Dependency to access the rate limiter from app state.
    
    Returns the rate limiter instance configured in the main app.
    """
    return request.app.state.limiter
