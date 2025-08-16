from rest_framework import serializers
from .models import AIGeneratedContent, SkillGapAnalysis, LearningPath

class AIGeneratedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIGeneratedContent
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

class LearningPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPath
        fields = '__all__'

class SkillGapAnalysisSerializer(serializers.ModelSerializer):
    learning_paths = LearningPathSerializer(many=True, read_only=True)
    
    class Meta:
        model = SkillGapAnalysis
        fields = '__all__'
        read_only_fields = ('user', 'created_at')