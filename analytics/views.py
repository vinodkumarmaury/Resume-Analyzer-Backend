from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import UserActivity, DashboardStats, JobViewAnalytics
from .serializers import UserActivitySerializer, DashboardStatsSerializer
from jobs.models import JobApplication
from resumes.models import ResumeAnalysis

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for the user"""
    
    stats, created = DashboardStats.objects.get_or_create(user=request.user)
    
    # Update stats
    stats.total_applications = JobApplication.objects.filter(applicant=request.user).count()
    stats.interviews_scheduled = JobApplication.objects.filter(
        applicant=request.user, 
        status='interview_scheduled'
    ).count()
    
    # Get latest resume analysis score
    latest_analysis = ResumeAnalysis.objects.filter(resume__user=request.user).first()
    if latest_analysis:
        stats.resume_score = latest_analysis.overall_score
    
    # Calculate average match score
    avg_match = JobApplication.objects.filter(
        applicant=request.user,
        match_score__isnull=False
    ).aggregate(avg_score=Avg('match_score'))
    
    if avg_match['avg_score']:
        stats.avg_match_score = avg_match['avg_score']
    
    stats.save()
    
    serializer = DashboardStatsSerializer(stats)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_trends(request):
    """Get application trends over time"""
    
    # Get applications from last 6 months
    six_months_ago = timezone.now() - timedelta(days=180)
    
    applications = JobApplication.objects.filter(
        applicant=request.user,
        applied_at__gte=six_months_ago
    ).extra(
        select={'month': "strftime('%%Y-%%m', applied_at)"}
    ).values('month').annotate(
        applications=Count('id'),
        interviews=Count('id', filter=models.Q(status='interview_scheduled'))
    ).order_by('month')
    
    # Format data for frontend
    trends_data = []
    for item in applications:
        month_name = timezone.datetime.strptime(item['month'], '%Y-%m').strftime('%b')
        trends_data.append({
            'month': month_name,
            'applications': item['applications'],
            'interviews': item['interviews']
        })
    
    return Response(trends_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def skill_progress(request):
    """Get skill progress data"""
    
    # This would typically track skill improvements over time
    # For now, we'll return mock data based on user skills
    user_skills = request.user.skills or []
    
    progress_data = []
    for skill in user_skills[:5]:  # Top 5 skills
        # Mock progress data - in production, this would track actual progress
        current = min(85 + hash(skill + request.user.username) % 15, 100)
        target = min(current + 10 + hash(skill) % 10, 100)
        
        progress_data.append({
            'skill': skill,
            'current': current,
            'target': target
        })
    
    return Response(progress_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_activity(request):
    """Get recent user activities"""
    
    activities = UserActivity.objects.filter(user=request.user)[:10]
    serializer = UserActivitySerializer(activities, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_activity(request):
    """Log user activity"""
    
    activity_type = request.data.get('activity_type')
    description = request.data.get('description')
    metadata = request.data.get('metadata', {})
    
    if not activity_type or not description:
        return Response(
            {"error": "activity_type and description are required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    activity = UserActivity.objects.create(
        user=request.user,
        activity_type=activity_type,
        description=description,
        metadata=metadata
    )
    
    serializer = UserActivitySerializer(activity)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_job_view(request):
    """Track job view for analytics"""
    
    job_id = request.data.get('job_id')
    if not job_id:
        return Response(
            {"error": "job_id is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from jobs.models import Job
        job = Job.objects.get(id=job_id)
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        JobViewAnalytics.objects.create(
            job=job,
            user=request.user,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({"message": "Job view tracked"}, status=status.HTTP_201_CREATED)
        
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )