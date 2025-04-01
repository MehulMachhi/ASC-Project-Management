from django.db import models

# Create your models here.
# rom django.db import models
from django.contrib.auth.models import User


class TestCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def _str_(self):
        return self.name

    class Meta:
        verbose_name_plural = "Test Categories"


class TestPriority(models.Model):
    name = models.CharField(max_length=50)  # e.g., P0, P1, P2, P3
    description = models.CharField(max_length=200)  # e.g., "Critical - Must test"
    order = models.PositiveSmallIntegerField(unique=True)

    def _str_(self):
        return f"{self.name} - {self.description}"

    class Meta:
        verbose_name_plural = "Test Priorities"
        ordering = ['order']


class TestEnvironment(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Production", "Staging", "QA"
    description = models.TextField(blank=True)
    base_url = models.URLField(blank=True)

    def _str_(self):
        return self.name


class TestCase(models.Model):
    STATUS_CHOICES = [
        ('draft' , 'Draft') ,
        ('ready' , 'Ready for Testing') ,
        ('in_progress' , 'In Progress') ,
        ('passed' , 'Passed') ,
        ('failed' , 'Failed') ,
        ('blocked' , 'Blocked') ,
        ('skipped' , 'Skipped') ,
    ]

    TYPE_CHOICES = [
        ('functional' , 'Functional Test') ,
        ('integration' , 'Integration Test') ,
        ('regression' , 'Regression Test') ,
        ('usability' , 'Usability Test') ,
        ('performance' , 'Performance Test') ,
        ('security' , 'Security Test') ,
        ('smoke' , 'Smoke Test') ,
        ('sanity' , 'Sanity Test') ,
    ]

    AUTOMATION_STATUS_CHOICES = [
        ('not_automated' , 'Not Automated') ,
        ('automated' , 'Automated') ,
        ('in_progress' , 'Automation In Progress') ,
        ('needs_update' , 'Automation Needs Update') ,
    ]

    # Basic Information
    project = models.ForeignKey('core.Project' , on_delete=models.CASCADE , related_name='project_cases')
    category = models.ForeignKey(TestCategory , on_delete=models.SET_NULL , null=True , related_name='test_cases')
    title = models.CharField(max_length=200)
    description = models.TextField(
        help_text="Provide a brief description of what this test case verifies"
    )

    # Classification
    priority = models.ForeignKey(TestPriority , on_delete=models.SET_NULL , null=True)
    test_type = models.CharField(max_length=20 , choices=TYPE_CHOICES , default='functional')
    automation_status = models.CharField(
        max_length=20 ,
        choices=AUTOMATION_STATUS_CHOICES ,
        default='not_automated'
    )

    # Prerequisites and Environment
    environment = models.ForeignKey(
        TestEnvironment ,
        on_delete=models.SET_NULL ,
        null=True ,
        help_text="Select the environment where this test should be executed"
    )
    prerequisites = models.TextField(
        blank=True ,
        help_text="List any prerequisites needed before executing this test case"
    )

    # Results
    status = models.CharField(max_length=20 , choices=STATUS_CHOICES , default='draft')
    actual_result = models.TextField(blank=True)
    comments = models.TextField(blank=True)

    # Attachments
    attachments = models.FileField(upload_to='test_cases/' , blank=True , null=True)

    # Dependencies
    dependent_on = models.ManyToManyField(
        'self' ,
        blank=True ,
        symmetrical=False ,
        related_name='dependent_test_cases'
    )

    # Assignment
    assigned_to = models.ForeignKey(
        User ,
        on_delete=models.SET_NULL ,
        null=True ,
        related_name='assigned_tests'
    )
    created_by = models.ForeignKey(
        User ,
        on_delete=models.PROTECT ,
        related_name='created_tests'
    )

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_time = models.DurationField(
        null=True ,
        blank=True ,
        help_text="Estimated time to execute this test case"
    )

    def _str_(self):
        return f"{self.project.name} - {self.title}"

    class Meta:
        ordering = ['-created_at']


class TestStep(models.Model):
    test_case = models.ForeignKey(TestCase , on_delete=models.CASCADE , related_name='steps')
    step_number = models.PositiveIntegerField()
    action = models.TextField(help_text="What action should be performed")
    expected_result = models.TextField(help_text="What is the expected outcome")
    actual_result = models.TextField(blank=True , help_text="What actually happened (fill during execution)")
    STATUS_CHOICES = [
        ('not_executed' , 'Not Executed') ,
        ('passed' , 'Passed') ,
        ('failed' , 'Failed') ,
        ('blocked' , 'Blocked') ,
        ('skipped' , 'Skipped') ,
    ]
    status = models.CharField(
        max_length=20 ,
        choices=STATUS_CHOICES ,
        default='not_executed'
    )
    screenshot = models.ImageField(
        upload_to='test_steps/' ,
        blank=True ,
        null=True ,
        help_text="Upload a screenshot if needed"
    )

    class Meta:
        ordering = ['step_number']
        unique_together = ['test_case' , 'step_number']

    def _str_(self):
        return f"Step {self.step_number} - {self.test_case.title}"