from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs
    path('', views.JobListCreateView.as_view(), name='job-list-create'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),
    path('<int:job_id>/apply/', views.apply_to_job, name='apply-to-job'),
    path('<int:job_id>/save/', views.save_job, name='save-job'),
    path('<int:job_id>/unsave/', views.unsave_job, name='unsave-job'),
    path('my-applications/', views.my_applications, name='my-applications'),
    path('saved/', views.saved_jobs, name='saved-jobs'),
    path('recommendations/', views.job_recommendations, name='job-recommendations'),
    
    # New recruiter endpoints
    path('recruiter/jobs/', views.recruiter_jobs, name='recruiter-jobs'),
    path('recruiter/jobs/<int:job_id>/applicants/', views.job_applicants, name='job-applicants'),
    path('recruiter/applications/<int:application_id>/status/', views.update_application_status, name='update-application-status'),
    path('recruiter/candidates/', views.recruiter_candidates, name='recruiter-candidates'),
    path('recruiter/jobs/<int:job_id>/delete/', views.delete_job, name='delete-job'),
    path('recruiter/jobs/<int:job_id>/update/', views.update_job, name='update-job'),
]