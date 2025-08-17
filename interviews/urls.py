from django.urls import path
from . import views

urlpatterns = [
    path('', views.InterviewListCreateView.as_view(), name='interview_list_create'),
    path('<int:pk>/', views.InterviewDetailView.as_view(), name='interview_detail'),
    path('schedule/', views.schedule_interview, name='schedule_interview'),
    path('list/', views.get_interviews, name='get_interviews'),
    path('<int:interview_id>/status/', views.update_interview_status, name='update_interview_status'),
    path('<int:interview_id>/reschedule/', views.reschedule_interview, name='reschedule_interview'),
]
