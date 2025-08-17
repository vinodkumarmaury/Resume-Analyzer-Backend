from django.urls import path
from . import views

urlpatterns = [
    path('generate-cover-letter/', views.generate_cover_letter_view, name='generate-cover-letter'),
    path('generate-cold-email/', views.generate_cold_email_view, name='generate-cold-email'),
    path('skill-gap-analysis/', views.skill_gap_analysis_view, name='skill-gap-analysis'),
    path('my-content/', views.user_ai_content, name='user-ai-content'),
    path('my-analyses/', views.user_skill_analyses, name='user-skill-analyses'),
    path('career-guidance/', views.career_guidance, name='career-guidance'),
]