from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserActivity(models.Model):
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('profile_update', 'Profile Update'),
        ('resume_upload', 'Resume Upload'),
        ('job_application', 'Job Application'),
        ('job_view', 'Job View'),
        ('skill_analysis', 'Skill Analysis'),
        ('cover_letter_generated', 'Cover Letter Generated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()}"

class DashboardStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_stats')
    total_applications = models.IntegerField(default=0)
    interviews_scheduled = models.IntegerField(default=0)
    profile_views = models.IntegerField(default=0)
    resume_score = models.FloatField(default=0.0)
    avg_match_score = models.FloatField(default=0.0)
    skills_improved = models.IntegerField(default=0)
    courses_taken = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Stats for {self.user.username}"

class JobViewAnalytics(models.Model):
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='view_analytics')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"View: {self.job.title} by {self.user.username if self.user else 'Anonymous'}"