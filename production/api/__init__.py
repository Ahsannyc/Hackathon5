"""
API Module - REST/gRPC API endpoints

Main FastAPI application with multi-channel integration:
- Gmail webhook integration
- WhatsApp/Twilio webhook integration
- Web form submission handler
"""

try:
    from .main import app
    __all__ = ["app"]
except ImportError:
    # Fallback if main.py not fully initialized
    __all__ = []
