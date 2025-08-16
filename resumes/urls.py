from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_resume, name='upload-resume'),
    path('', views.get_resume, name='get-resume'),
    path('analyze/', views.analyze_resume_view, name='analyze-resume'),
    path('analyses/', views.resume_analyses, name='resume-analyses'),
]