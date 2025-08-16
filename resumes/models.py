from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Resume(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resume')
    file = models.FileField(upload_to='resumes/')
    original_filename = models.CharField(max_length=255)
    extracted_text = models.TextField(blank=True)
    parsed_data = models.JSONField(default=dict, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Resume"

class ResumeAnalysis(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='analyses')
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, null=True, blank=True)
    overall_score = models.FloatField()
    ats_score = models.FloatField()
    strengths = models.JSONField(default=list)
    improvements = models.JSONField(default=list)
    missing_keywords = models.JSONField(default=list)
    section_scores = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analysis for {self.resume.user.username}'s Resume"

class SkillExtraction(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skill_extractions')
    extracted_skills = models.JSONField(default=list)
    confidence_scores = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Skills for {self.resume.user.username}"