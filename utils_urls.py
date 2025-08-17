from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from django.conf import settings
import sys

@api_view(['GET'])
@permission_classes([AllowAny])
def backend_status(request):
    """Get backend status and version info"""
    return Response({
        "status": "online",
        "version": "1.0.0",
        "django_version": sys.version,
        "debug_mode": settings.DEBUG,
        "database": "connected" if connection.ensure_connection() else "disconnected",
        "message": "Resume Analyzer Backend is running"
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    try:
        # Test database connection
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    return Response({
        "status": "healthy",
        "database": db_status,
        "timestamp": request.META.get('HTTP_DATE', 'unknown')
    })

urlpatterns = [
    path('backend-status/', backend_status, name='backend-status'),
    path('health/', health_check, name='health-check'),
]
