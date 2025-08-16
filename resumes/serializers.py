from rest_framework import serializers
from .models import Resume, ResumeAnalysis, SkillExtraction

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = '__all__'
        read_only_fields = ('user', 'uploaded_at', 'updated_at')

class ResumeAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeAnalysis
        fields = '__all__'

class SkillExtractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillExtraction
        fields = '__all__'