from django.urls import path, include
from . import views
from .views import candidate_profile

urlpatterns = [
    path('api/auth/', include('authentication.urls')),
    path('generate-cover-letter/', views.generate_cover_letter_view, name='generate-cover-letter'),
    path('generate-cold-email/', views.generate_cold_email_view, name='generate-cold-email'),
    path('skill-gap-analysis/', views.skill_gap_analysis_view, name='skill-gap-analysis'),
    path('my-content/', views.user_ai_content, name='user-ai-content'),
    path('my-analyses/', views.user_skill_analyses, name='user-skill-analyses'),
    path('career-guidance/', views.career_guidance, name='career-guidance'),
    path('applications/<int:application_id>/candidate/', candidate_profile, name='candidate-profile'),
    path('api/jobs/', include('jobs.urls')),
]