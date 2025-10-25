"""
Middleware package for request processing
"""
from src.middleware.auth_middleware import AuthMiddleware

__all__ = ["AuthMiddleware"]
