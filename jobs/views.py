from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from resumes.utils import calculate_skill_match_score
from .models import Job, JobApplication, SavedJob
from .serializers import JobSerializer, JobApplicationSerializer, SavedJobSerializer

class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.filter(status='active')
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['job_type', 'location', 'company']
    search_fields = ['title', 'company', 'description', 'skills']
    ordering_fields = ['created_at', 'salary_min', 'salary_max']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)

class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated()]
        return [AllowAny()]

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_to_job(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
        
        # Check if already applied
        if JobApplication.objects.filter(job=job, applicant=request.user).exists():
            return Response(
                {"error": "You have already applied to this job"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cover_letter = request.data.get('cover_letter', '')
        
        # If no cover letter provided, generate a basic one
        if not cover_letter:
            cover_letter = f"""Dear Hiring Manager,

I am writing to express my interest in the {job.title} position at {job.company}. 
I believe my skills and experience make me a strong candidate for this role.

I look forward to the opportunity to discuss how I can contribute to your team.

Best regards,
{request.user.first_name} {request.user.last_name}"""
        
        application = JobApplication.objects.create(
            job=job,
            applicant=request.user,
            cover_letter=cover_letter
        )
        
        serializer = JobApplicationSerializer(application)
        return Response({
            "success": True,
            "message": "Application submitted successfully",
            "application": serializer.data,
            "next_steps": [
                "Your application has been sent to the recruiter",
                "You will be notified of any updates",
                "You can track your application status in 'My Applications'"
            ]
        }, status=status.HTTP_201_CREATED)
        
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_applications(request):
    applications = JobApplication.objects.filter(applicant=request.user)
    serializer = JobApplicationSerializer(applications, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_job(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
        saved_job, created = SavedJob.objects.get_or_create(user=request.user, job=job)
        
        if created:
            return Response({
                "message": "Job bookmarked successfully",
                "job_id": job_id,
                "is_saved": True
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "message": "Job already bookmarked",
                "job_id": job_id,
                "is_saved": True
            }, status=status.HTTP_200_OK)
            
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unsave_job(request, job_id):
    try:
        saved_job = SavedJob.objects.get(user=request.user, job_id=job_id)
        saved_job.delete()
        return Response({
            "message": "Job bookmark removed successfully",
            "job_id": job_id,
            "is_saved": False
        }, status=status.HTTP_200_OK)
    except SavedJob.DoesNotExist:
        return Response({
            "message": "Job was not bookmarked",
            "job_id": job_id,
            "is_saved": False
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def saved_jobs(request):
    saved_jobs = SavedJob.objects.filter(user=request.user)
    serializer = SavedJobSerializer(saved_jobs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_recommendations(request):
    """
    Get job recommendations for the authenticated user
    """
    try:
        # Get user's skills and preferences for recommendations
        user = request.user
        
        # Placeholder recommendations - replace with actual logic
        recommendations = [
            {
                "id": 1,
                "title": "Senior Software Engineer",
                "company": "TechCorp Inc.",
                "location": "Remote",
                "salary_range": "$80,000 - $120,000",
                "match_score": 95,
                "description": "Looking for experienced developers...",
                "required_skills": ["Python", "Django", "React"],
                "posted_date": "2024-08-15"
            },
            {
                "id": 2,
                "title": "Full Stack Developer",
                "company": "WebDev Solutions",
                "location": "New York, NY",
                "salary_range": "$70,000 - $100,000",
                "match_score": 88,
                "description": "Join our dynamic team...",
                "required_skills": ["JavaScript", "Node.js", "PostgreSQL"],
                "posted_date": "2024-08-16"
            },
            {
                "id": 3,
                "title": "Frontend Developer",
                "company": "Design Studio",
                "location": "San Francisco, CA",
                "salary_range": "$65,000 - $90,000",
                "match_score": 82,
                "description": "Creative frontend role...",
                "required_skills": ["React", "CSS", "TypeScript"],
                "posted_date": "2024-08-17"
            }
        ]
        
        return Response({
            "recommendations": recommendations,
            "count": len(recommendations),
            "message": "Job recommendations retrieved successfully"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": "Failed to fetch job recommendations",
            "detail": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recruiter_jobs(request):
    """Get jobs posted by the current recruiter"""
    if request.user.role != 'recruiter':
        return Response(
            {"error": "Only recruiters can access this endpoint"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    jobs = Job.objects.filter(posted_by=request.user)
    serializer = JobSerializer(jobs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_applicants(request, job_id):
    """Get all applicants for a specific job"""
    try:
        job = Job.objects.get(id=job_id, posted_by=request.user)
        applications = JobApplication.objects.filter(job=job).select_related('applicant')
        serializer = JobApplicationSerializer(applications, many=True)
        return Response(serializer.data)
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found or you don't have permission"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_application_status(request, application_id):
    """Update the status of a job application"""
    try:
        application = JobApplication.objects.get(
            id=application_id, 
            job__posted_by=request.user
        )
        
        new_status = request.data.get('status')
        if new_status not in dict(JobApplication.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = new_status
        application.save()
        
        serializer = JobApplicationSerializer(application)
        return Response(serializer.data)
        
    except JobApplication.DoesNotExist:
        return Response(
            {"error": "Application not found or you don't have permission"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recruiter_candidates(request):
    """Get all candidates who applied to recruiter's jobs"""
    if request.user.role != 'recruiter':
        return Response(
            {"error": "Only recruiters can access this endpoint"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    applications = JobApplication.objects.filter(
        job__posted_by=request.user
    ).select_related('applicant', 'job')
    
    # Apply filters from query parameters
    skills = request.GET.get('skills')
    experience = request.GET.get('experience')
    location = request.GET.get('location')
    limit = request.GET.get('limit')
    
    if skills:
        skills_list = [skill.strip() for skill in skills.split(',')]
        applications = applications.filter(
            applicant__skills__overlap=skills_list
        )
    
    if experience:
        applications = applications.filter(
            applicant__experience_level=experience
        )
    
    if location:
        applications = applications.filter(
            applicant__location__icontains=location
        )
    
    # Apply limit if provided
    if limit:
        try:
            limit_int = int(limit)
            applications = applications[:limit_int]
        except ValueError:
            pass
    
    serializer = JobApplicationSerializer(applications, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_job(request, job_id):
    """Delete a job posting (recruiter only)"""
    try:
        job = Job.objects.get(id=job_id, posted_by=request.user)
        job.delete()
        return Response({"message": "Job deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found or you don't have permission"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_job(request, job_id):
    """Update a job posting (recruiter only)"""
    try:
        job = Job.objects.get(id=job_id, posted_by=request.user)
        serializer = JobSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found or you don't have permission"}, 
            status=status.HTTP_404_NOT_FOUND
        )