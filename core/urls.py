# core/urls.py
from django.urls import include
from rest_framework.routers import DefaultRouter
from . import views

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView, logout

router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet)
router.register(r'teams', views.TeamViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'time-entries', views.TimeEntryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/' , CustomTokenObtainPairView.as_view() , name='token_obtain_pair') ,
    path('auth/refresh/' , TokenRefreshView.as_view() , name='token_refresh') ,
    path('auth/logout/' , logout , name='auth_logout') ,
]