"""
API module for HTN 2025 Backend
Contains API clients, routes, and related utilities
"""

from .gemini_api import GeminiAPI
from .routes import api

__all__ = ['GeminiAPI', 'api']