from django.contrib import admin
from .models import Interview

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('job', 'candidate', 'recruiter', 'scheduled_date', 'status', 'interview_type')
    list_filter = ('status', 'interview_type', 'scheduled_date')
    search_fields = ('job__title', 'candidate__email', 'recruiter__email')
    ordering = ['-scheduled_date']
