from rest_framework import serializers
from .models import Job, JobApplication, SavedJob
from authentication.serializers import UserSerializer
from resumes.utils import calculate_skill_match_score
from django.utils import timezone
from datetime import timedelta

class JobSerializer(serializers.ModelSerializer):
    posted_by = UserSerializer(read_only=True)
    applications_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()
    expires_at = serializers.DateTimeField(required=False)
    
    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ('posted_by', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        # Set default expiration date if not provided (30 days from now)
        if 'expires_at' not in validated_data:
            validated_data['expires_at'] = timezone.now() + timedelta(days=30)
        return super().create(validated_data)
    
    def get_applications_count(self, obj):
        return obj.applications.count()
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedJob.objects.filter(user=request.user, job=obj).exists()
        return False
    
    def get_match_score(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.skills:
            return round(calculate_skill_match_score(request.user.skills, obj.skills), 1)
        return None

class JobApplicationSerializer(serializers.ModelSerializer):
    applicant = UserSerializer(read_only=True)
    job = JobSerializer(read_only=True)
    
    class Meta:
        model = JobApplication
        fields = '__all__'
        read_only_fields = ('applicant', 'applied_at', 'updated_at')

class SavedJobSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    
    class Meta:
        model = SavedJob
        fields = '__all__'
        read_only_fields = ('user', 'saved_at')