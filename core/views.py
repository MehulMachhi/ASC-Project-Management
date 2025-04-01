from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from datetime import datetime, timedelta

# Fix imports to use relative imports from the core app
from .models import Employee, Task, Team, TeamMembership, Project, Comment, TimeEntry
from .serializers import (
    EmployeeSerializer, TaskSerializer, TeamSerializer,
    TeamDetailSerializer, ProjectSerializer, ProjectDetailSerializer,
    TaskDetailSerializer, CommentSerializer, TimeEntrySerializer
)

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

@permission_classes([AllowAny])
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = get_user_model().objects.get(username=request.data['username'])
            user_data = UserSerializer(user).data
            response.data['user'] = user_data
        return response

@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    response = Response({"message": "Successfully logged out"})
    return response

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['position', 'department', 'is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'position']
    ordering_fields = ['user__username', 'position', 'department']

    @action(detail=True)
    def tasks(self, request, pk=None):
        employee = self.get_object()
        tasks = Task.objects.filter(assigned_to=employee)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update']:
            return TeamDetailSerializer
        return TeamSerializer

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        team = self.get_object()
        employee_id = request.data.get('employee_id')
        role = request.data.get('role', 'member')

        try:
            employee = Employee.objects.get(id=employee_id)
            TeamMembership.objects.create(
                team=team,
                employee=employee,
                role=role
            )
            return Response({'status': 'member added'})
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employee not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'team', 'is_archived']
    search_fields = ['name', 'description']
    ordering_fields = ['start_date', 'end_date', 'status']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update']:
            return ProjectDetailSerializer
        return ProjectSerializer

    @action(detail=True)
    def tasks_summary(self, request, pk=None):
        project = self.get_object()
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(status='completed').count()
        overdue_tasks = project.tasks.filter(
            due_date__lt=datetime.now().date(),
            status__in=['pending', 'in_progress']
        ).count()

        return Response({
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'overdue_tasks': overdue_tasks,
            'completion_percentage': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        })

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'project', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'priority', 'status']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update']:
            return TaskDetailSerializer
        return TaskSerializer

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        task = self.get_object()
        status = request.data.get('status')

        if status not in dict(task.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        task.status = status
        if status == 'completed':
            task.completion_percentage = 100
        task.save()

        return Response({'status': 'task status updated'})

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['task', 'author']
    search_fields = ['content']

class TimeEntryViewSet(viewsets.ModelViewSet):
    queryset = TimeEntry.objects.all()
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['task', 'employee', 'date']
    ordering_fields = ['date', 'hours_spent']

    def get_queryset(self):
        if self.request.user.is_superuser:
            return TimeEntry.objects.all()
        return TimeEntry.objects.filter(employee__user=self.request.user)