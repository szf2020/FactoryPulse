from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Third-party Imports (JWT Authentication)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Local Imports
from core.views import RegisterView, trigger_task_view, check_task_status_view

urlpatterns = [
    # Django Admin Interface
    path('admin/', admin.site.urls),

    # Core Application Routes (Business Logic)
    path('api/', include('core.urls')),

    # Authentication Endpoints (JWT & Registration)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login (Get Access/Refresh Pair)
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # Refresh Access Token
    path('api/register/', RegisterView.as_view(), name='auth_register'),          # New User Registration
    
    # Celery Task Endpoints
    path('api/tasks/trigger/', trigger_task_view, name='trigger_task'),           
    path('api/tasks/<str:task_id>/status/', check_task_status_view, name='status_task'),
]

# Serve user-uploaded media files (images) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)