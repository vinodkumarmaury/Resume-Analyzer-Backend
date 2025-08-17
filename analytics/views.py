from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import UserActivity, DashboardStats, JobViewAnalytics
from .serializers import UserActivitySerializer, DashboardStatsSerializer
from jobs.models import JobApplication
from resumes.models import ResumeAnalysis
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for the user"""
    
    logger.info(f"Dashboard stats requested by user: {request.user.username}")
    
    stats, created = DashboardStats.objects.get_or_create(user=request.user)
    
    # Update stats
    stats.total_applications = JobApplication.objects.filter(applicant=request.user).count()
    stats.interviews_scheduled = JobApplication.objects.filter(
        applicant=request.user, 
        status='interview_scheduled'
    ).count()
    
    # Get latest resume analysis score
    try:
        latest_analysis = ResumeAnalysis.objects.filter(resume__user=request.user).first()
        if latest_analysis:
            stats.resume_score = latest_analysis.overall_score
    except:
        stats.resume_score = 0
    
    # Calculate average match score
    avg_match = JobApplication.objects.filter(
        applicant=request.user,
        match_score__isnull=False
    ).aggregate(avg_score=Avg('match_score'))
    
    if avg_match['avg_score']:
        stats.avg_match_score = avg_match['avg_score']
    
    stats.save()
    
    serializer = DashboardStatsSerializer(stats)
    logger.info(f"Dashboard stats response: {serializer.data}")
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_trends(request):
    """Get application trends over time"""
    
    logger.info(f"Application trends requested by user: {request.user.username}")
    
    try:
        # Get applications from last 6 months
        six_months_ago = timezone.now() - timedelta(days=180)
        
        applications = JobApplication.objects.filter(
            applicant=request.user,
            applied_at__gte=six_months_ago
        ).extra(
            select={'month': "strftime('%%Y-%%m', applied_at)"}
        ).values('month').annotate(
            applications=Count('id'),
            interviews=Count('id', filter=Q(status='interview_scheduled'))
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
        
        # If no data, return empty array for last 6 months
        if not trends_data:
            current_date = timezone.now()
            for i in range(6):
                month_date = current_date - timedelta(days=30*i)
                trends_data.append({
                    'month': month_date.strftime('%b'),
                    'applications': 0,
                    'interviews': 0
                })
            trends_data.reverse()
        
        logger.info(f"Application trends response: {trends_data}")
        return Response(trends_data)
    
    except Exception as e:
        logger.error(f"Application trends error: {str(e)}")
        # Return empty array to prevent frontend errors
        return Response([])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def skill_progress(request):
    """Get skill progress data"""
    
    logger.info(f"Skill progress requested by user: {request.user.username}")
    
    try:
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
        
        logger.info(f"Skill progress response: {progress_data}")
        return Response(progress_data)
    
    except Exception as e:
        logger.error(f"Skill progress error: {str(e)}")
        return Response([])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_activity(request):
    """Get recent user activities"""
    
    logger.info(f"Recent activity requested by user: {request.user.username}")
    
    try:
        activities = UserActivity.objects.filter(user=request.user)[:10]
        serializer = UserActivitySerializer(activities, many=True)
        logger.info(f"Recent activity response: {serializer.data}")
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Recent activity error: {str(e)}")
        return Response([])

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
    
    try:
        activity = UserActivity.objects.create(
            user=request.user,
            activity_type=activity_type,
            description=description,
            metadata=metadata
        )
        
        serializer = UserActivitySerializer(activity)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {"error": "Failed to log activity", "detail": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
    except Exception as e:
        return Response(
            {"error": "Failed to track job view", "detail": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recruiter_dashboard_stats(request):
    """Get dashboard statistics for recruiters"""
    
    if request.user.role != 'recruiter':
        return Response(
            {"error": "Only recruiters can access this endpoint"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        from jobs.models import Job
        
        # Get recruiter's jobs
        recruiter_jobs = Job.objects.filter(posted_by=request.user)
        
        # Calculate stats
        total_jobs = recruiter_jobs.count()
        active_jobs = recruiter_jobs.filter(status='active').count()
        total_applications = JobApplication.objects.filter(job__posted_by=request.user).count()
        
        # Applications by status
        pending_applications = JobApplication.objects.filter(
            job__posted_by=request.user, 
            status='pending'
        ).count()
        
        interviews_scheduled = JobApplication.objects.filter(
            job__posted_by=request.user, 
            status='interview_scheduled'
        ).count()
        
        hired_candidates = JobApplication.objects.filter(
            job__posted_by=request.user, 
            status='hired'
        ).count()
        
        # Recent applications (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_applications = JobApplication.objects.filter(
            job__posted_by=request.user,
            applied_at__gte=thirty_days_ago
        ).count()
        
        stats = {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'interviews_scheduled': interviews_scheduled,
            'hired_candidates': hired_candidates,
            'recent_applications': recent_applications,
            'avg_applications_per_job': round(total_applications / max(total_jobs, 1), 1)
        }
        
        logger.info(f"Recruiter dashboard stats: {stats}")
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Recruiter dashboard stats error: {str(e)}")
        return Response(
            {"error": "Failed to fetch dashboard stats", "detail": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )