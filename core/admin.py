from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count , Sum , Avg
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    Employee , Team , TeamMembership , Project ,
    Task , Comment , TimeEntry
)
from django.db import models


# Employee Admin
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user' , 'position' , 'department' , 'phone' , 'is_active')
    list_filter = ('is_active' , 'position' , 'department', 'user', 'phone', 'address', 'skills',)
    search_fields = ('user__username' , 'user__first_name' , 'user__last_name' , 'position' , 'department')
    raw_id_fields = ('user' ,)

    fieldsets = (
        ('User Information' , {
            'fields': ('user' , 'position' , 'department')
        }) ,
        ('Contact Information' , {
            'fields': ('phone' , 'address')
        }) ,
        ('Professional Details' , {
            'fields': ('skills' , 'hourly_rate')
        }) ,
        ('Status' , {
            'fields': ('is_active' , 'profile_image')
        }) ,
    )


class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name_plural = 'Employee Profile'


class CustomUserAdmin(UserAdmin):
    inlines = (EmployeeInline ,)
    list_display = ('username' , 'email' , 'first_name' , 'last_name' , 'get_position' , 'is_active')

    def get_position(self , obj):
        return obj.employee.position if hasattr(obj , 'employee') else '-'

    get_position.short_description = 'Position'


# Unregister the default UserAdmin and register with custom
admin.site.unregister(User)
admin.site.register(User , CustomUserAdmin)


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 1
    autocomplete_fields = ['employee']


class ProjectInline(admin.TabularInline):
    model = Project
    extra = 0
    show_change_link = True
    fields = ('name' , 'status' , 'start_date' , 'end_date' , 'priority')
    readonly_fields = ('status' ,)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name' , 'team_lead' , 'member_count' , 'active_projects_count' , 'is_active')
    list_filter = ('is_active' , 'created_at')
    search_fields = ('name' , 'description' , 'team_lead__user__username')
    inlines = [TeamMembershipInline , ProjectInline]
    autocomplete_fields = ['team_lead']

    def get_queryset(self , request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            member_count=Count('members' , distinct=True) ,
            active_projects_count=Count(
                'projects' ,
                filter=models.Q(projects__status__in=['not_started' , 'in_progress']) ,
                distinct=True
            )
        )

    def member_count(self , obj):
        return obj.member_count

    member_count.admin_order_field = 'member_count'

    def active_projects_count(self , obj):
        return obj.active_projects_count

    active_projects_count.admin_order_field = 'active_projects_count'

    actions = ['activate_teams' , 'deactivate_teams']

    def activate_teams(self , request , queryset):
        queryset.update(is_active=True)

    activate_teams.short_description = "Mark selected teams as active"

    def deactivate_teams(self , request , queryset):
        queryset.update(is_active=False)

    deactivate_teams.short_description = "Mark selected teams as inactive"


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    show_change_link = True
    fields = ('title' , 'assigned_to' , 'due_date' , 'status' , 'priority')
    readonly_fields = ('status' ,)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name' , 'team' , 'project_manager' , 'start_date' , 'end_date' ,
                    'status' , 'priority' , 'budget_status')
    list_filter = ('status' , 'priority' , 'team' , 'is_archived')
    search_fields = ('name' , 'description' , 'team__name' , 'project_manager__user__username')
    readonly_fields = ('created_at' , 'updated_at')
    inlines = [TaskInline]
    autocomplete_fields = ['team' , 'project_manager']

    fieldsets = (
        ('Basic Information' , {
            'fields': ('name' , 'description' , 'team' , 'project_manager')
        }) ,
        ('Timeline' , {
            'fields': ('start_date' , 'end_date')
        }) ,
        ('Status & Priority' , {
            'fields': ('status' , 'priority' , 'is_archived')
        }) ,
        ('Financial' , {
            'fields': ('budget' ,)
        }) ,
        ('Additional Information' , {
            'fields': ('github_repo' , 'tags') ,
            'classes': ('collapse' ,)
        }) ,
        ('System Fields' , {
            'fields': ('created_at' , 'updated_at') ,
            'classes': ('collapse' ,)
        }) ,
    )

    # def task_completion_ratio(self , obj):
    #     total_tasks = obj.tasks.count()
    #     if total_tasks == 0:
    #         return "No tasks"
    #     completed_tasks = obj.tasks.filter(status='completed').count()
    #     percentage = (completed_tasks / total_tasks) * 100
    #     return(
    #         '<div style="width:100px; background-color: #f8f9fa; border: 1px solid #dee2e6;">'
    #         '<div style="width: {}%; background-color: #28a745; color: white; text-align: center;">'
    #         '{:.0f}%</div></div>' ,
    #         percentage , percentage
    #     )

    # task_completion_ratio.short_description = 'Completion'

    def budget_status(self , obj):
        if not obj.budget:
            return "No budget set"
        total_cost = TimeEntry.objects.filter(
            task__project=obj
        ).aggregate(
            total=Sum('hours_spent')
        )['total'] or 0
        return f"${total_cost:,.2f} / ${obj.budget:,.2f}"

    actions = ['archive_projects' , 'unarchive_projects']

    def archive_projects(self , request , queryset):
        queryset.update(is_archived=True)

    archive_projects.short_description = "Archive selected projects"

    def unarchive_projects(self , request , queryset):
        queryset.update(is_archived=False)

    unarchive_projects.short_description = "Unarchive selected projects"


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at' ,)


class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 0
    readonly_fields = ('created_at' ,)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title' , 'project' , 'assigned_to' , 'due_date' , 'status' ,
                    'priority' , 'time_logged' , 'completion_percentage')
    list_filter = ('status' , 'priority' , 'project__team' , 'project')
    search_fields = ('title' , 'description' , 'assigned_to__user__username')
    readonly_fields = ('created_at' , 'updated_at')
    inlines = [CommentInline , TimeEntryInline]
    autocomplete_fields = ['project' , 'assigned_to' , 'parent_task' , 'dependencies']

    def time_logged(self , obj):
        total_hours = obj.time_entries.aggregate(
            total=Sum('hours_spent')
        )['total'] or 0
        estimated = obj.estimated_hours or 0
        if estimated:
            return f"{total_hours:.1f}hrs / {estimated:.1f}hrs"
        return f"{total_hours:.1f}hrs"

    actions = ['mark_completed' , 'mark_in_progress']

    def mark_completed(self , request , queryset):
        queryset.update(status='completed' , completion_percentage=100)

    mark_completed.short_description = "Mark selected tasks as completed"

    def mark_in_progress(self , request , queryset):
        queryset.update(status='in_progress')

    mark_in_progress.short_description = "Mark selected tasks as in progress"


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('employee' , 'task' , 'date' , 'hours_spent' , 'created_at')
    list_filter = ('date' , 'employee' , 'task__project')
    search_fields = ('employee__user__username' , 'task__title' , 'description')
    readonly_fields = ('created_at' , 'updated_at')
    autocomplete_fields = ['task' , 'employee']

    def get_queryset(self , request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            return queryset.filter(employee__user=request.user)
        return queryset


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task' , 'author' , 'content_preview' , 'created_at')
    list_filter = ('created_at' , 'author' , 'task__project')
    search_fields = ('content' , 'author__user__username' , 'task__title')
    readonly_fields = ('created_at' , 'updated_at')
    autocomplete_fields = ['task' , 'author']

    def content_preview(self , obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Content'


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('team' , 'employee' , 'role' , 'joined_date' , 'left_date')
    list_filter = ('team' , 'role' , 'joined_date')
    search_fields = ('team__name' , 'employee__user__username' , 'role')
    autocomplete_fields = ['team' , 'employee']


# Customize admin site header and title
admin.site.site_header = 'Project Management System'
admin.site.site_title = 'PMS Admin Portal'
admin.site.index_title = 'Welcome to PMS Admin Portal'