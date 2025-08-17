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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_analytics(request):
    """Enhanced analytics for candidates"""
    user = request.user
    
    # Basic stats
    applications = JobApplication.objects.filter(applicant=user)
    total_applications = applications.count()
    
    # Application status breakdown
    status_breakdown = applications.values('status').annotate(count=Count('id'))
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_applications = applications.filter(applied_at__gte=thirty_days_ago).count()
    
    # Success rate calculation
    positive_responses = applications.filter(
        status__in=['interview_scheduled', 'accepted', 'hired']
    ).count()
    success_rate = (positive_responses / total_applications * 100) if total_applications > 0 else 0
    
    # Top skills from applied jobs
    from jobs.models import Job
    applied_jobs = Job.objects.filter(
        id__in=applications.values_list('job_id', flat=True)
    )
    
    # Industry breakdown
    industry_stats = applied_jobs.values('category').annotate(count=Count('id'))
    
    # Location preferences
    location_stats = applied_jobs.values('location').annotate(count=Count('id'))
    
    # Salary range analysis
    avg_min_salary = applied_jobs.aggregate(avg_min=Avg('salary_min'))['avg_min'] or 0
    avg_max_salary = applied_jobs.aggregate(avg_max=Avg('salary_max'))['avg_max'] or 0
    
    # Response time analysis
    responded_applications = applications.exclude(status='pending')
    avg_response_days = 7  # Placeholder - would need additional tracking
    
    analytics_data = {
        "total_applications": total_applications,
        "recent_applications_30_days": recent_applications,
        "success_rate": round(success_rate, 1),
        "average_response_time_days": avg_response_days,
        "status_breakdown": list(status_breakdown),
        "top_categories": list(industry_stats[:5]),
        "preferred_locations": list(location_stats[:5]),
        "salary_insights": {
            "average_min_salary": round(avg_min_salary, 2),
            "average_max_salary": round(avg_max_salary, 2),
            "target_range": f"${avg_min_salary:,.0f} - ${avg_max_salary:,.0f}" if avg_min_salary > 0 else "Not available"
        },
        "recommendations": [
            f"Apply to {max(5-recent_applications, 0)} more jobs this month" if recent_applications < 5 else "Great job staying active!",
            "Consider expanding to new categories" if len(industry_stats) < 3 else "Good category diversification",
            f"Your success rate is {'excellent' if success_rate > 20 else 'good' if success_rate > 10 else 'needs improvement'}"
        ]
    }
    
    return Response(analytics_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recruiter_analytics(request):
    """Enhanced analytics for recruiters"""
    user = request.user
    
    # Only show analytics for recruiters
    if user.role != 'recruiter':
        return Response(
            {"error": "Access denied. Recruiter role required."}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Jobs posted by this recruiter
    from jobs.models import Job
    jobs = Job.objects.filter(posted_by=user)
    total_jobs = jobs.count()
    
    # Applications received
    applications = JobApplication.objects.filter(job__posted_by=user)
    total_applications = applications.count()
    
    # Applications per job
    avg_applications_per_job = total_applications / total_jobs if total_jobs > 0 else 0
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_jobs = jobs.filter(created_at__gte=thirty_days_ago).count()
    recent_applications = applications.filter(applied_at__gte=thirty_days_ago).count()
    
    # Job status breakdown
    active_jobs = jobs.filter(status='active').count()
    inactive_jobs = jobs.exclude(status='active').count()
    
    # Top performing jobs (by application count)
    top_jobs = jobs.annotate(
        app_count=Count('jobapplication')
    ).order_by('-app_count')[:5]
    
    # Application status breakdown
    status_breakdown = applications.values('status').annotate(count=Count('id'))
    
    # Popular job categories
    category_stats = jobs.values('category').annotate(count=Count('id'))
    
    # Salary insights
    avg_min_salary = jobs.aggregate(avg_min=Avg('salary_min'))['avg_min'] or 0
    avg_max_salary = jobs.aggregate(avg_max=Avg('salary_max'))['avg_max'] or 0
    
    # Location insights
    location_stats = jobs.values('location').annotate(count=Count('id'))
    
    analytics_data = {
        "total_jobs_posted": total_jobs,
        "total_applications_received": total_applications,
        "average_applications_per_job": round(avg_applications_per_job, 1),
        "active_jobs": active_jobs,
        "inactive_jobs": inactive_jobs,
        "recent_activity_30_days": {
            "new_jobs": recent_jobs,
            "new_applications": recent_applications
        },
        "application_status_breakdown": list(status_breakdown),
        "top_performing_jobs": [
            {
                "title": job.title,
                "company": job.company,
                "applications": job.app_count,
                "id": job.id
            } for job in top_jobs
        ],
        "job_categories": list(category_stats),
        "location_distribution": list(location_stats),
        "salary_insights": {
            "average_min_salary": round(avg_min_salary, 2),
            "average_max_salary": round(avg_max_salary, 2),
            "market_range": f"${avg_min_salary:,.0f} - ${avg_max_salary:,.0f}" if avg_min_salary > 0 else "Not available"
        },
        "performance_insights": [
            f"Your jobs receive {avg_applications_per_job:.1f} applications on average",
            "Most popular category" if category_stats else "Consider posting in different categories",
            f"Posted {recent_jobs} jobs this month" if recent_jobs > 0 else "Consider posting more jobs to attract talent"
        ]
    }
    
    return Response(analytics_data)