from django.urls import path
from . import views

urlpatterns = [
    path('', views.InterviewListCreateView.as_view(), name='interview-list-create'),
    path('<int:pk>/', views.InterviewDetailView.as_view(), name='interview-detail'),
    path('<int:interview_id>/status/', views.update_interview_status, name='update-interview-status'),
]
