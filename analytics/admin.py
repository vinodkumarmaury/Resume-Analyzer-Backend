from django.contrib import admin
from .models import UserActivity,DashboardStats, JobViewAnalytics

admin.site.register(UserActivity)
admin.site.register(DashboardStats)
admin.site.register(JobViewAnalytics)