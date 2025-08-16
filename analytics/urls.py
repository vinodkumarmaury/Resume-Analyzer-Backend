from django.urls import path
from . import views

urlpatterns = [
    path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
    path('application-trends/', views.application_trends, name='application-trends'),
    path('skill-progress/', views.skill_progress, name='skill-progress'),
    path('recent-activity/', views.recent_activity, name='recent-activity'),
    path('log-activity/', views.log_activity, name='log-activity'),
    path('track-job-view/', views.track_job_view, name='track-job-view'),
]