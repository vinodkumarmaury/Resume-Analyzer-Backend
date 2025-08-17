from django.db import models
from django.contrib.auth import get_user_model
from jobs.models import Job

User = get_user_model()

class Interview(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    TYPE_CHOICES = [
        ('phone', 'Phone'),
        ('video', 'Video'),
        ('in_person', 'In Person'),
        ('technical', 'Technical'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='interviews')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='candidate_interviews')
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recruiter_interviews')
    scheduled_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    interview_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='video')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    location = models.CharField(max_length=200, blank=True)  # for in-person or video link
    notes = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    rating = models.IntegerField(null=True, blank=True)  # 1-5 scale
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"Interview for {self.job.title} - {self.candidate.get_full_name()}"
