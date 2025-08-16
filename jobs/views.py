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
        
        application = JobApplication.objects.create(
            job=job,
            applicant=request.user,
            cover_letter=request.data.get('cover_letter', '')
        )
        
        serializer = JobApplicationSerializer(application)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
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
            return Response({"message": "Job saved successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Job already saved"}, status=status.HTTP_200_OK)
            
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unsave_job(request, job_id):
    try:
        saved_job = SavedJob.objects.get(user=request.user, job_id=job_id)
        saved_job.delete()
        return Response({"message": "Job unsaved successfully"}, status=status.HTTP_200_OK)
    except SavedJob.DoesNotExist:
        return Response({"error": "Job not in saved list"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def saved_jobs(request):
    saved_jobs = SavedJob.objects.filter(user=request.user)
    serializer = SavedJobSerializer(saved_jobs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_recommendations(request):
    """Get AI-powered job recommendations for the user"""
    user_skills = request.user.skills or []
    
    if not user_skills:
        # If no skills, return recent jobs
        jobs = Job.objects.filter(status='active').order_by('-created_at')[:10]
    else:
        # Get jobs that match user skills
        jobs = Job.objects.filter(
            status='active',
            skills__overlap=user_skills
        ).order_by('-created_at')[:20]
        
        # Calculate match scores for each job
        job_scores = []
        for job in jobs:
            match_score = calculate_skill_match_score(user_skills, job.skills)
            job_scores.append((job, match_score))
        
        # Sort by match score and take top 10
        job_scores.sort(key=lambda x: x[1], reverse=True)
        jobs = [job for job, score in job_scores[:10]]
    