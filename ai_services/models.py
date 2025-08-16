from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AIGeneratedContent(models.Model):
    CONTENT_TYPES = [
        ('cover_letter', 'Cover Letter'),
        ('cold_email', 'Cold Email'),
        ('skill_analysis', 'Skill Analysis'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_content')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, null=True, blank=True)
    prompt = models.TextField()
    generated_content = models.TextField()
    tone = models.CharField(max_length=50, default='professional')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_content_type_display()} for {self.user.username}"

class SkillGapAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_analyses')
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE)
    current_skills = models.JSONField(default=list)
    required_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    skill_match_score = models.FloatField()
    learning_recommendations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Skill Analysis: {self.user.username} -> {self.job.title}"

class LearningPath(models.Model):
    skill_analysis = models.ForeignKey(SkillGapAnalysis, on_delete=models.CASCADE, related_name='learning_paths')
    skill = models.CharField(max_length=100)
    courses = models.JSONField(default=list)
    estimated_duration = models.CharField(max_length=50)
    priority = models.IntegerField(default=1)
    
    def __str__(self):
        return f"Learning path for {self.skill}"