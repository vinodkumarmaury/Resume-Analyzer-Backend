from rest_framework import serializers
from .models import UserActivity, DashboardStats, JobViewAnalytics

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

class DashboardStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardStats
        fields = '__all__'
        read_only_fields = ('user', 'updated_at')

class JobViewAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobViewAnalytics
        fields = '__all__'