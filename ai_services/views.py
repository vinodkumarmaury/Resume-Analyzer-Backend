from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import AIGeneratedContent, SkillGapAnalysis
from .serializers import AIGeneratedContentSerializer, SkillGapAnalysisSerializer
from .utils import generate_cover_letter, generate_cold_email, analyze_skill_gap
from jobs.models import Job
from authentication.serializers import UserSerializer

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def career_guidance(request):
    """Provide personalized career guidance"""
    try:
        query = request.data.get('query', '')
        user_role = request.user.role
        user_skills = request.user.skills or []
        
        # Generate contextual career advice
        if 'resume' in query.lower():
            advice = {
                "type": "resume_help",
                "title": "Resume Optimization Tips",
                "recommendations": [
                    "Use action verbs to start each bullet point",
                    "Quantify your achievements with numbers and percentages",
                    "Tailor your resume for each job application",
                    "Include relevant keywords from the job description",
                    "Keep your resume to 1-2 pages maximum"
                ],
                "next_steps": [
                    "Upload your resume for AI analysis",
                    "Review our ATS optimization guide",
                    "Practice with our resume builder tool"
                ]
            }
        elif 'interview' in query.lower():
            advice = {
                "type": "interview_prep",
                "title": "Interview Preparation Guide",
                "recommendations": [
                    "Research the company and role thoroughly",
                    "Prepare STAR method examples for behavioral questions",
                    "Practice technical questions relevant to your field",
                    "Prepare thoughtful questions to ask the interviewer",
                    "Plan your outfit and arrive 10-15 minutes early"
                ],
                "next_steps": [
                    "Schedule mock interviews",
                    "Review common interview questions",
                    "Prepare your elevator pitch"
                ]
            }
        elif 'career change' in query.lower() or 'transition' in query.lower():
            advice = {
                "type": "career_transition",
                "title": "Career Transition Strategy",
                "recommendations": [
                    "Identify transferable skills from your current role",
                    "Network with professionals in your target industry",
                    "Consider additional certifications or training",
                    "Start with freelance or contract work to gain experience",
                    "Update your LinkedIn profile to reflect your new direction"
                ],
                "next_steps": [
                    "Complete our skill gap analysis",
                    "Explore relevant online courses",
                    "Join professional associations in your target field"
                ]
            }
        elif 'salary' in query.lower() or 'negotiate' in query.lower():
            advice = {
                "type": "salary_negotiation",
                "title": "Salary Negotiation Tips",
                "recommendations": [
                    "Research market rates for your role and location",
                    "Document your achievements and value-add",
                    "Practice your negotiation conversation",
                    "Consider the total compensation package",
                    "Be prepared to walk away if necessary"
                ],
                "next_steps": [
                    "Use salary comparison tools",
                    "Prepare a compensation proposal",
                    "Schedule a meeting with your manager"
                ]
            }
        else:
            # General career advice
            advice = {
                "type": "general_guidance",
                "title": "Career Development Recommendations",
                "recommendations": [
                    f"Build expertise in {', '.join(user_skills[:3]) if user_skills else 'your field'}",
                    "Develop both technical and soft skills",
                    "Build a strong professional network",
                    "Stay updated with industry trends",
                    "Seek feedback and mentorship opportunities"
                ],
                "next_steps": [
                    "Set SMART career goals",
                    "Create a professional development plan",
                    "Join relevant online communities"
                ]
            }
        
        # Add personalized elements based on user data
        advice["personalized_tips"] = []
        if user_role == 'job_seeker':
            advice["personalized_tips"].extend([
                "Focus on building a strong portfolio",
                "Optimize your job search strategy",
                "Consider remote work opportunities"
            ])
        
        if user_skills:
            advice["skill_recommendations"] = [
                f"Continue developing {skill}" for skill in user_skills[:3]
            ]
        
        advice["resources"] = [
            {"title": "Industry Reports", "type": "reading", "url": "#"},
            {"title": "Online Courses", "type": "learning", "url": "#"},
            {"title": "Networking Events", "type": "networking", "url": "#"},
            {"title": "Career Coaching", "type": "mentorship", "url": "#"}
        ]
        
        return Response({
            "success": True,
            "advice": advice,
            "user_context": {
                "role": user_role,
                "skills_count": len(user_skills),
                "query": query
            },
            "generated_at": timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": "Failed to generate career guidance", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_profile(request, application_id):
    """
    Recruiter can view the full profile of a candidate for a specific application.
    """
    try:
        application = JobApplication.objects.get(id=application_id)
        # Only allow recruiters who posted the job to view
        if application.job.posted_by != request.user:
            return Response({'error': 'Not authorized.'}, status=403)
        candidate = application.applicant
        data = UserSerializer(candidate).data
        return Response(data)
    except JobApplication.DoesNotExist:
        return Response({'error': 'Application not found.'}, status=404)