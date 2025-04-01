from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime


class TimeStampedModel(models.Model):
    """Abstract base class with created and modified timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Employee(TimeStampedModel):
    user = models.OneToOneField(User , on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    phone = models.CharField(max_length=15 , blank=True , null=True)
    address = models.TextField(blank=True , null=True)
    department = models.CharField(max_length=100 , blank=True)
    skills = models.TextField(blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=10 , decimal_places=2 , null=True , blank=True)
    is_active = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to='employee_profiles/' , null=True , blank=True)

    def __str__(self):
        return self.user.get_full_name()

    class Meta:
        ordering = ['user__first_name' , 'user__last_name']


class Team(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(Employee , related_name="teams" , through='TeamMembership')
    team_lead = models.ForeignKey(
        Employee ,
        on_delete=models.SET_NULL ,
        null=True ,
        related_name='leading_teams'
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class TeamMembership(TimeStampedModel):
    team = models.ForeignKey(Team , on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee , on_delete=models.CASCADE)
    role = models.CharField(max_length=50 , default='member')
    joined_date = models.DateField(default=timezone.now)
    left_date = models.DateField(null=True , blank=True)

    class Meta:
        unique_together = ('team' , 'employee')


class Project(TimeStampedModel):
    STATUS_CHOICES = [
        ('not_started' , 'Not Started') ,
        ('planning' , 'Planning') ,
        ('in_progress' , 'In Progress') ,
        ('on_hold' , 'On Hold') ,
        ('completed' , 'Completed') ,
        ('cancelled' , 'Cancelled')
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(blank=True , null=True)
    status = models.CharField(max_length=20 , choices=STATUS_CHOICES , default='not_started')
    team = models.ForeignKey(Team , on_delete=models.CASCADE , related_name="projects")
    project_manager = models.ForeignKey(
        Employee ,
        on_delete=models.SET_NULL ,
        null=True ,
        related_name='managed_projects'
    )
    budget = models.DecimalField(max_digits=12 , decimal_places=2 , null=True , blank=True)
    priority = models.CharField(
        max_length=20 ,
        choices=[('low' , 'Low') , ('medium' , 'Medium') , ('high' , 'High')] ,
        default='medium'
    )
    github_repo = models.URLField(blank=True , null=True)
    tags = models.JSONField(default=list , blank=True)
    is_archived = models.BooleanField(default=False)

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError('End date cannot be before start date')

    def save(self , *args , **kwargs):
        self.full_clean()
        super().save(*args , **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-start_date' , 'name']


class Task(TimeStampedModel):
    STATUS_CHOICES = [
        ('backlog' , 'Backlog') ,
        ('pending' , 'Pending') ,
        ('in_progress' , 'In Progress') ,
        ('in_review' , 'In Review') ,
        ('completed' , 'Completed') ,
        ('cancelled' , 'Cancelled')
    ]

    project = models.ForeignKey(Project , on_delete=models.CASCADE , related_name="tasks")
    parent_task = models.ForeignKey(
        'self' ,
        null=True ,
        blank=True ,
        on_delete=models.CASCADE ,
        related_name='subtasks'
    )
    assigned_to = models.ForeignKey(Employee , on_delete=models.SET_NULL , null=True , blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    estimated_hours = models.DecimalField(max_digits=6 , decimal_places=2 , null=True , blank=True)
    actual_hours = models.DecimalField(max_digits=6 , decimal_places=2 , null=True , blank=True)
    status = models.CharField(max_length=20 , choices=STATUS_CHOICES , default='pending')
    priority = models.CharField(
        max_length=20 ,
        choices=[('low' , 'Low') , ('medium' , 'Medium') , ('high' , 'High')] ,
        default='medium'
    )
    completion_percentage = models.IntegerField(default=0)
    dependencies = models.ManyToManyField('self' , blank=True , symmetrical=False)
    attachments = models.JSONField(default=list , blank=True)

    def clean(self):
        if self.due_date and self.due_date < self.project.start_date:
            raise ValidationError('Task due date cannot be before project start date')
        if self.project.end_date and self.due_date > self.project.end_date:
            raise ValidationError('Task due date cannot be after project end date')
        if self.completion_percentage < 0 or self.completion_percentage > 100:
            raise ValidationError('Completion percentage must be between 0 and 100')

    def save(self , *args , **kwargs):
        self.full_clean()
        super().save(*args , **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['due_date' , 'priority']


class Comment(TimeStampedModel):
    task = models.ForeignKey(Task , on_delete=models.CASCADE , related_name='comments')
    author = models.ForeignKey(Employee , on_delete=models.CASCADE)
    content = models.TextField()
    attachments = models.JSONField(default=list , blank=True)

    def __str__(self):
        return f'Comment by {self.author} on {self.task}'

    class Meta:
        ordering = ['-created_at']


class TimeEntry(TimeStampedModel):
    task = models.ForeignKey(Task , on_delete=models.CASCADE , related_name='time_entries')
    employee = models.ForeignKey(Employee , on_delete=models.CASCADE)
    date = models.DateField()
    hours_spent = models.DecimalField(max_digits=5 , decimal_places=2)
    description = models.TextField(blank=True)

    def clean(self):
        if self.hours_spent <= 0:
            raise ValidationError('Hours spent must be greater than 0')
        if self.date > timezone.now().date():
            raise ValidationError('Cannot log time for future dates')

    def save(self , *args , **kwargs):
        self.full_clean()
        super().save(*args , **kwargs)

    def __str__(self):
        return f'{self.employee} - {self.task} - {self.hours_spent}hrs'

    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Time entries'