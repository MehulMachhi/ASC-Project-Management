from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import TestCase , TestCategory , TestPriority , TestEnvironment , TestStep


class TestStepInline(admin.TabularInline):
    model = TestStep
    extra = 1  # Number of empty forms to display
    fields = ('step_number' , 'action' , 'expected_result' , 'actual_result' , 'status' , 'screenshot')
    ordering = ['step_number']

    def get_extra(self , request , obj=None , **kwargs):
        """Return 3 empty forms when creating new test case, 1 when editing"""
        if obj is None:
            return 3
        return 1


class TestStepAdminForm(forms.ModelForm):
    class Meta:
        model = TestStep
        fields = '__all__'
        widgets = {
            'action': forms.Textarea(attrs={'rows': 3}) ,
            'expected_result': forms.Textarea(attrs={'rows': 3}) ,
            'actual_result': forms.Textarea(attrs={'rows': 3}) ,
        }


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ('name' , 'description')
    search_fields = ('name' , 'description')


@admin.register(TestPriority)
class TestPriorityAdmin(admin.ModelAdmin):
    list_display = ('name' , 'description' , 'order')
    ordering = ['order']


@admin.register(TestEnvironment)
class TestEnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name' , 'base_url')
    search_fields = ('name' , 'description')


@admin.register(TestCase)
class TestCaseAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [TestStepInline]

    list_display = (
        'title' ,
        'project' ,
        'category' ,
        'priority' ,
        'test_type' ,
        'status' ,
        'assigned_to' ,
        'created_at' ,
        'steps_count' ,
        'execution_status'
    )

    list_filter = (
        'status' ,
        'project' ,
        'category' ,
        'priority' ,
        'test_type' ,
        'automation_status' ,
        'environment' ,
        'assigned_to'
    )

    search_fields = (
        'title' ,
        'description' ,
        'project__name'
    )

    readonly_fields = (
        'created_at' ,
        'updated_at' ,
        'created_by' ,
        'steps_count' ,
        'execution_status'
    )

    autocomplete_fields = ['project' , 'dependent_on']

    fieldsets = (
        ('Basic Information' , {
            'fields': (
                ('project' , 'category') ,
                'title' ,
                'description' ,
            )
        }) ,
        ('Classification' , {
            'fields': (
                ('priority' , 'test_type') ,
                'automation_status' ,
            )
        }) ,
        ('Environment & Prerequisites' , {
            'fields': (
                'environment' ,
                'prerequisites' ,
            )
        }) ,
        ('Results & Status' , {
            'fields': (
                ('status' , 'execution_status') ,
                'actual_result' ,
                'comments' ,
                'attachments' ,
            )
        }) ,
        ('Relations & Assignment' , {
            'fields': (
                'dependent_on' ,
                ('assigned_to' , 'steps_count') ,
                'estimated_time' ,
            )
        }) ,
        ('Metadata' , {
            'fields': ('created_by' , 'created_at' , 'updated_at') ,
            'classes': ('collapse' ,)
        }) ,
    )

    def steps_count(self , obj):
        return obj.steps.count()

    steps_count.short_description = 'Number of Steps'

    def execution_status(self , obj):
        steps = obj.steps.all()
        if not steps:
            return 'No Steps'

        total = steps.count()
        passed = steps.filter(status='passed').count()
        failed = steps.filter(status='failed').count()
        not_executed = steps.filter(status='not_executed').count()

        if not_executed == total:
            return format_html('<span style="color: #666;">Not Started</span>')
        elif failed > 0:
            return format_html('<span style="color: #dc3545;">Failed ({}/{})</span>' , passed , total)
        elif passed == total:
            return format_html('<span style="color: #28a745;">Passed ({}/{})</span>' , passed , total)
        else:
            return format_html('<span style="color: #ffc107;">In Progress ({}/{})</span>' , passed , total)

    execution_status.short_description = 'Execution Status'

    def save_model(self , request , obj , form , change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request , obj , form , change)

    def save_formset(self , request , form , formset , change):
        instances = formset.save(commit=False)

        # Delete marked for deletion
        for obj in formset.deleted_objects:
            obj.delete()

        # Add/update instances
        for instance in instances:
            if not instance.step_number:  # If step_number is not set
                # Get the highest step number and add 1
                last_step = instance.test_case.steps.order_by('-step_number').first()
                instance.step_number = (last_step.step_number + 1) if last_step else 1
            instance.save()

        formset.save_m2m()

    def get_queryset(self , request):
        qs = super().get_queryset(request)
        return qs.select_related('project' , 'category' , 'priority' , 'assigned_to')

    class Media:
        css = {
            'all': ('admin/css/forms.css' ,)
        }
        js = ('admin/js/jquery.init.js' ,)


# Optional: Register TestStep model separately if you want to manage them independently
@admin.register(TestStep)
class TestStepAdmin(admin.ModelAdmin):
    list_display = ('test_case' , 'step_number' , 'action' , 'status')
    list_filter = ('status' , 'test_case__project')
    search_fields = ('action' , 'expected_result' , 'test_case__title')
    ordering = ['test_case' , 'step_number']
    form = TestStepAdminForm