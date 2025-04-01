from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Employee , Team , TeamMembership , Project , Task , Comment , TimeEntry
from django.db import models
from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id' , 'username' , 'first_name' , 'last_name' , 'email')
        read_only_fields = ('id' ,)


class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    teams = serializers.PrimaryKeyRelatedField(many=True , read_only=True)

    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ('id' , 'created_at' , 'updated_at')

    def create(self , validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create(**user_data)
        employee = Employee.objects.create(user=user , **validated_data)
        return employee


class TeamMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMembership
        fields = '__all__'
        read_only_fields = ('id' , 'created_at' , 'updated_at')


class TeamSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()
    active_projects_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = '__all__'
        read_only_fields = ('id' , 'created_at' , 'updated_at')

    def get_members_count(self , obj):
        return obj.members.count()

    def get_active_projects_count(self , obj):
        return obj.projects.filter(status__in=['not_started' , 'in_progress']).count()


class TeamDetailSerializer(TeamSerializer):
    members = EmployeeSerializer(many=True , read_only=True)
    team_lead = EmployeeSerializer(read_only=True)


class ProjectSerializer(serializers.ModelSerializer):
    completion_percentage = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('id' , 'created_at' , 'updated_at')

    def get_completion_percentage(self , obj):
        total_tasks = obj.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = obj.tasks.filter(status='completed').count()
        return (completed_tasks / total_tasks) * 100

    def get_task_count(self , obj):
        return obj.tasks.count()


class ProjectDetailSerializer(ProjectSerializer):
    team = TeamSerializer(read_only=True)
    project_manager = EmployeeSerializer(read_only=True)


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ('id' , 'created_at' , 'updated_at')


class TaskDetailSerializer(TaskSerializer):
    project = ProjectSerializer(read_only=True)
    assigned_to = EmployeeSerializer(read_only=True)
    subtasks = serializers.SerializerMethodField()
    time_logged = serializers.SerializerMethodField()

    def get_subtasks(self , obj):
        return TaskSerializer(obj.subtasks.all() , many=True).data

    def get_time_logged(self , obj):
        return obj.time_entries.aggregate(total_hours=models.Sum('hours_spent'))['total_hours'] or 0


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('id' , 'created_at' , 'updated_at')


class TimeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeEntry
        fields = '__all__'
        read_only_fields = ('id' , 'created_at' , 'updated_at')