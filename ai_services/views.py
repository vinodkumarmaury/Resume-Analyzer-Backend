from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import AIGeneratedContent, SkillGapAnalysis
from .serializers import AIGeneratedContentSerializer, SkillGapAnalysisSerializer
from .utils import generate_cover_letter, generate_cold_email, analyze_skill_gap
from jobs.models import Job

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_cover_letter_view(request):
    job_id = request.data.get('job_id')
    tone = request.data.get('tone', 'professional')
    custom_prompt = request.data.get('custom_prompt', '')
    
    if not job_id:
        return Response(
            {"error": "Job ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        job = Job.objects.get(id=job_id)
        content = generate_cover_letter(request.user, job, tone, custom_prompt)
        
        ai_content = AIGeneratedContent.objects.create(
            user=request.user,
            content_type='cover_letter',
            job=job,
            prompt=f"Generate cover letter for {job.title} at {job.company}",
            generated_content=content,
            tone=tone
        )
        
        serializer = AIGeneratedContentSerializer(ai_content)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to generate cover letter: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_cold_email_view(request):
    job_id = request.data.get('job_id')
    recruiter_email = request.data.get('recruiter_email', 'recruiter@company.com')
    
    if not job_id:
        return Response(
            {"error": "Job ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        job = Job.objects.get(id=job_id)
        content = generate_cold_email(request.user, job, recruiter_email)
        
        ai_content = AIGeneratedContent.objects.create(
            user=request.user,
            content_type='cold_email',
            job=job,
            prompt=f"Generate cold email for {job.title} at {job.company}",
            generated_content=content
        )
        
        serializer = AIGeneratedContentSerializer(ai_content)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to generate cold email: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def skill_gap_analysis_view(request):
    job_id = request.data.get('job_id')
    
    if not job_id:
        return Response(
            {"error": "Job ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        job = Job.objects.get(id=job_id)
        analysis = analyze_skill_gap(request.user, job)
        
        serializer = SkillGapAnalysisSerializer(analysis)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to analyze skill gap: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_ai_content(request):
    content = AIGeneratedContent.objects.filter(user=request.user).order_by('-created_at')
    serializer = AIGeneratedContentSerializer(content, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_skill_analyses(request):
    analyses = SkillGapAnalysis.objects.filter(user=request.user).order_by('-created_at')
    serializer = SkillGapAnalysisSerializer(analyses, many=True)
    return Response(serializer.data)