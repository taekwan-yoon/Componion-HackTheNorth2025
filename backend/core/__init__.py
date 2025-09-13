"""
Core module for HTN 2025 Backend
Contains database models and connection utilities
"""

from .db import engine
from .models import Session, SessionUser, ChatMessage, VideoAnalysis, VideoProcessingStatus

__all__ = ['engine', 'Session', 'SessionUser', 'ChatMessage', 'VideoAnalysis', 'VideoProcessingStatus']