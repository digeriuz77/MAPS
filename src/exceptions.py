"""
Custom exceptions for the character-ai-chat application
"""

class LLMServiceError(Exception):
    """Exception raised by LLM service operations"""
    pass

class APIKeyError(LLMServiceError):
    """Exception raised when API keys are missing or invalid"""
    pass

class ModelNotSupportedError(LLMServiceError):
    """Exception raised when a model is not supported"""
    pass

class ResponseGenerationError(LLMServiceError):
    """Exception raised when response generation fails"""
    pass