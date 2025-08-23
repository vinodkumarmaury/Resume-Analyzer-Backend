from rest_framework import serializers
from .models import Job, JobApplication, SavedJob
from authentication.serializers import UserSerializer
from resumes.utils import calculate_skill_match_score
from django.utils import timezone
from datetime import timedelta

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'company', 'location']

class JobApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = JobApplication
        fields = ['id', 'job', 'status', 'applied_at']

class SavedJobSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    
    class Meta:
        model = SavedJob
        fields = '__all__'
        read_only_fields = ('user', 'saved_at')