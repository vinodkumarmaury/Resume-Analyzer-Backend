from django.urls import path
from jobs import views as job_views
from analytics import views as analytics_views

# Recruiter-specific URL patterns to match frontend expectations
urlpatterns = [
    # Dashboard stats
    path('dashboard/stats/', analytics_views.recruiter_dashboard_stats, name='recruiter-dashboard-stats'),
    
    # Job management
    path('jobs/', job_views.recruiter_jobs, name='recruiter-jobs'),
    path('jobs/<int:job_id>/applicants/', job_views.job_applicants, name='recruiter-job-applicants'),
    
    # Application management
    path('applications/<int:application_id>/status/', job_views.update_application_status, name='recruiter-update-application-status'),
    
    # Candidate management
    path('candidates/', job_views.recruiter_candidates, name='recruiter-candidates'),
]
