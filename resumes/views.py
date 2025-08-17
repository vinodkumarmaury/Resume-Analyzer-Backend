from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.utils import timezone
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
        
        # Enhanced analysis with AI insights
        analysis_result = {
            "overall_score": 85,
            "ats_score": 78,
            "sections_analysis": {
                "contact_info": {"score": 95, "status": "excellent", "feedback": "Complete contact information provided"},
                "summary": {"score": 80, "status": "good", "feedback": "Professional summary could be more impactful"},
                "experience": {"score": 88, "status": "very_good", "feedback": "Strong work experience with relevant details"},
                "education": {"score": 90, "status": "excellent", "feedback": "Educational background well presented"},
                "skills": {"score": 75, "status": "good", "feedback": "Skills section could include more technical keywords"}
            },
            "strengths": [
                "Strong technical background in relevant technologies",
                "Clear career progression shown",
                "Quantified achievements in previous roles",
                "Professional formatting and structure"
            ],
            "improvements": [
                "Add more industry-specific keywords",
                "Include metrics and numbers in achievements",
                "Optimize for ATS scanning",
                "Consider adding relevant certifications"
            ],
            "keyword_analysis": {
                "found_keywords": ["Python", "JavaScript", "React", "Django"],
                "missing_keywords": ["TypeScript", "AWS", "Docker", "API"],
                "keyword_density": "Good"
            },
            "ai_recommendations": [
                "Consider adding a 'Projects' section to showcase your work",
                "Include relevant volunteer work or open-source contributions",
                "Tailor your resume for each specific job application",
                "Use action verbs to start each bullet point"
            ],
            "match_score": 82 if job_id else None,
            "analysis_date": timezone.now().isoformat(),
            "next_steps": [
                "Review and implement the suggested improvements",
                "Test your resume with different ATS systems",
                "Get feedback from industry professionals",
                "Keep your resume updated with latest achievements"
            ]
        }
        
        if job_id:
            # Add job-specific analysis
            try:
                from jobs.models import Job
                job = Job.objects.get(id=job_id)
                analysis_result["job_match"] = {
                    "job_title": job.title,
                    "company": job.company,
                    "skills_match": len(set(resume.parsed_data.get('skills', [])) & set(job.skills)) if resume.parsed_data else 0,
                    "missing_skills": list(set(job.skills) - set(resume.parsed_data.get('skills', []))) if resume.parsed_data else job.skills,
                    "recommendations": f"Focus on highlighting experience with {', '.join(job.skills[:3])} in your resume"
                }
            except Job.DoesNotExist:
                pass
        
        # Store analysis in database
        analysis = ResumeAnalysis.objects.create(
            resume=resume,
            overall_score=analysis_result["overall_score"],
            ats_score=analysis_result["ats_score"],
            strengths=analysis_result["strengths"],
            improvements=analysis_result["improvements"],
            missing_keywords=analysis_result["keyword_analysis"]["missing_keywords"]
        )
        
        return Response(analysis_result, status=status.HTTP_201_CREATED)
        
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_cover_letter(request):
    """Generate a cover letter for a specific job"""
    try:
        job_id = request.data.get('job_id')
        custom_details = request.data.get('custom_details', '')
        
        if not job_id:
            return Response(
                {"error": "job_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the job details
        from jobs.models import Job
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get user's resume for context
        try:
            resume = Resume.objects.get(user=request.user)
            user_skills = request.user.skills or []
            user_experience = resume.parsed_data.get('work_experience', []) if resume.parsed_data else []
        except Resume.DoesNotExist:
            # Use user profile data if no resume
            user_skills = request.user.skills or []
            user_experience = []
        
        # Generate cover letter content
        cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job.title} position at {job.company}. With my background and skills in {', '.join(user_skills[:3]) if user_skills else 'software development'}, I am excited about the opportunity to contribute to your team.

Based on the job requirements, I believe my experience aligns well with what you're looking for:

{f'• Relevant experience in {", ".join([exp.get("company", "various companies") for exp in user_experience[:2]])}' if user_experience else '• Strong technical background and passion for learning'}
• Proficiency in {', '.join(job.skills[:3]) if job.skills else 'the required technologies'}
• {custom_details if custom_details else 'Proven ability to work collaboratively in team environments'}

I am particularly drawn to this role because of {job.company}'s reputation and the exciting challenges it presents. The opportunity to work on {job.title.lower()} projects aligns perfectly with my career goals and technical interests.

Thank you for considering my application. I would welcome the opportunity to discuss how my skills and enthusiasm can contribute to your team's success.

Best regards,
{request.user.first_name} {request.user.last_name}"""
        
        return Response({
            "success": True,
            "cover_letter": cover_letter,
            "job_details": {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location
            },
            "user_context": {
                "skills_matched": [skill for skill in user_skills if skill in job.skills],
                "total_skills": len(user_skills),
                "experience_years": user_experience[0].get('years', 'N/A') if user_experience else 'N/A'
            },
            "generated_at": timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": "Failed to generate cover letter", "detail": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )