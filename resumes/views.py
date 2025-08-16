from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.storage import default_storage
from .models import Resume, ResumeAnalysis
from .serializers import ResumeSerializer, ResumeAnalysisSerializer
from .utils import parse_resume, analyze_resume

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_resume(request):
    if 'file' not in request.FILES:
        return Response(
            {"error": "No file provided"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['file']
    
    # Validate file type
    if not file.name.lower().endswith(('.pdf', '.docx')):
        return Response(
            {"error": "Only PDF and DOCX files are allowed"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Delete existing resume if any
    try:
        existing_resume = Resume.objects.get(user=request.user)
        existing_resume.file.delete()
        existing_resume.delete()
    except Resume.DoesNotExist:
        pass
    
    # Create new resume
    resume = Resume.objects.create(
        user=request.user,
        file=file,
        original_filename=file.name
    )
    
    # Parse resume content
    try:
        extracted_text, parsed_data = parse_resume(resume.file.path)
        resume.extracted_text = extracted_text
        resume.parsed_data = parsed_data
        resume.save()
        
        # Update user's resume_uploaded status
        request.user.resume_uploaded = True
        request.user.save()
        
        serializer = ResumeSerializer(resume)
        return Response({
            "resume": serializer.data,
            "message": "Resume uploaded and parsed successfully"
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        resume.delete()
        return Response(
            {"error": f"Failed to parse resume: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resume(request):
    try:
        resume = Resume.objects.get(user=request.user)
        serializer = ResumeSerializer(resume)
        return Response(serializer.data)
    except Resume.DoesNotExist:
        return Response(
            {"error": "No resume found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_resume_view(request):
    try:
        resume = Resume.objects.get(user=request.user)
        job_id = request.data.get('job_id')
        
        analysis = analyze_resume(resume, job_id)
        
        serializer = ResumeAnalysisSerializer(analysis)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Resume.DoesNotExist:
        return Response(
            {"error": "No resume found. Please upload a resume first."}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Analysis failed: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resume_analyses(request):
    try:
        resume = Resume.objects.get(user=request.user)
        analyses = ResumeAnalysis.objects.filter(resume=resume).order_by('-created_at')
        serializer = ResumeAnalysisSerializer(analyses, many=True)
        return Response(serializer.data)
    except Resume.DoesNotExist:
        return Response(
            {"error": "No resume found"}, 
            status=status.HTTP_404_NOT_FOUND
        )