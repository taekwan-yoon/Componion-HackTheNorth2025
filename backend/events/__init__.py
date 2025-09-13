"""
Events module for HTN 2025 Backend
Contains WebSocket event handlers
"""

from .socket_events import init_socket_events

__all__ = ['init_socket_events']