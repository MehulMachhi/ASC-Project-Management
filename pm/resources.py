# In resources.py
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import TestCase, TestStep

class TestStepResource(resources.ModelResource):
    test_case_title = fields.Field(
        column_name='test_case_title', 
        attribute='test_case', 
        widget=ForeignKeyWidget(TestCase, 'title')
    )
    
    class Meta:
        model = TestStep
        fields = ('id', 'test_case_title', 'step_number', 'action', 'expected_result', 'actual_result', 'status')


class TestCaseResource(resources.ModelResource):
    steps = fields.Field(column_name='steps', attribute='steps', readonly=True)
    
    class Meta:
        model = TestCase
        fields = (
            'id',
            'title',
            'project',
            'category',
            'priority',
            'test_type',
            'automation_status',
            'status',
            'assigned_to',
            'created_by',
            'created_at',
            'updated_at',
            "environment",
            "prerequisites",
            "actual_result",
            "comments",
            "attachments",
            "dependent_on",
            "estimated_time",
            "description",
            'steps', 
        )
    
    def dehydrate_steps(self, obj):
        """
        Return a string of all test steps for this test case.
        Format: Step 1: Action -> Expected Result | Step 2: ...
        """
        return " | ".join(
            f"Step {step.step_number}: {step.action} - {step.expected_result} - {step.actual_result} - {step.status} - {step.screenshot}"
            for step in obj.steps.all().order_by('step_number')
        )