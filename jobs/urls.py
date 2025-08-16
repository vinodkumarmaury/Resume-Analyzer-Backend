from django.urls import path
from . import views

urlpatterns = [
    path('', views.JobListCreateView.as_view(), name='job-list-create'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),
    path('<int:job_id>/apply/', views.apply_to_job, name='apply-to-job'),
    path('<int:job_id>/save/', views.save_job, name='save-job'),
    path('<int:job_id>/unsave/', views.unsave_job, name='unsave-job'),
    path('my-applications/', views.my_applications, name='my-applications'),
    path('saved/', views.saved_jobs, name='saved-jobs'),
    path('recommendations/', views.job_recommendations, name='job-recommendations'),
]