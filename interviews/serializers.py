from rest_framework import serializers
from .models import Interview
from authentication.serializers import UserSerializer
from jobs.serializers import JobSerializer

class InterviewSerializer(serializers.ModelSerializer):
    candidate = UserSerializer(read_only=True)
    recruiter = UserSerializer(read_only=True)
    job = JobSerializer(read_only=True)
    
    class Meta:
        model = Interview
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class InterviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = ['job', 'candidate', 'scheduled_date', 'duration_minutes', 
                 'interview_type', 'location', 'notes']
    
    def create(self, validated_data):
        validated_data['recruiter'] = self.context['request'].user
        return super().create(validated_data)
