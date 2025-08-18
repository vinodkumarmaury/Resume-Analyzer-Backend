import google.generativeai as genai
from django.conf import settings
from resumes.utils import calculate_skill_match_score
from .models import SkillGapAnalysis, LearningPath

def generate_cover_letter(user, job, tone='professional', custom_prompt=''):
    """Generate a personalized cover letter using Gemini AI"""
    # Use direct API key for deployment reliability
    GEMINI_API_KEY = "AIzaSyAb4pCUvMuCyiL_Y3clHlBa6DG6o_axUwg"
    
    if not GEMINI_API_KEY:
        print("Gemini AI configuration failed: GEMINI_API_KEY not set.")
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    # Build the prompt
    prompt = f"""
    Generate a professional cover letter for the following job application:
    
    Job Title: {job.title}
    Company: {job.company}
    Location: {job.location}
    Job Description: {job.description[:500]}...
    Required Skills: {', '.join(job.skills)}
    
    Applicant Information:
    Name: {user.first_name} {user.last_name}
    Email: {user.email}
    Experience Level: {user.experience_level}
    Skills: {', '.join(user.skills) if user.skills else 'Not specified'}
    Location: {user.location}
    
    Tone: {tone}
    
    Additional Instructions: {custom_prompt}
    
    Please generate a compelling cover letter that:
    1. Addresses the hiring manager professionally
    2. Shows enthusiasm for the role and company
    3. Highlights relevant skills and experience
    4. Demonstrates knowledge of the company/role
    5. Includes a strong call to action
    6. Is approximately 3-4 paragraphs long
    
    Format the letter properly with appropriate salutation and closing.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text if response.text else generate_template_cover_letter(user, job, tone)
    except Exception as e:
        print(f"Gemini API error: {e}")
        # Fallback to template-based generation
        return generate_template_cover_letter(user, job, tone)

def generate_cold_email(user, job, recruiter_email):
    """Generate a cold email to recruiters using Gemini AI"""
    # Use direct API key for deployment reliability
    GEMINI_API_KEY = "AIzaSyAb4pCUvMuCyiL_Y3clHlBa6DG6o_axUwg"
    
    if not GEMINI_API_KEY:
        print("Gemini AI configuration failed: GEMINI_API_KEY not set.")
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    Generate a professional cold email for reaching out to a recruiter about a job opportunity:
    
    Job Title: {job.title}
    Company: {job.company}
    
    Sender Information:
    Name: {user.first_name} {user.last_name}
    Email: {user.email}
    Experience Level: {user.experience_level}
    Skills: {', '.join(user.skills) if user.skills else 'Not specified'}
    Location: {user.location}
    
    Please generate a cold email that:
    1. Has a compelling subject line
    2. Is concise and professional
    3. Shows genuine interest in the company
    4. Highlights relevant qualifications
    5. Includes a clear call to action
    6. Is personalized and not generic
    7. Is approximately 150-200 words
    
    Format: Subject: [Subject Line]
    
    [Email Body]
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text if response.text else generate_template_cold_email(user, job, recruiter_email)
    except Exception as e:
        print(f"Gemini API error: {e}")
        # Fallback to template-based generation
        return generate_template_cold_email(user, job, recruiter_email)

def analyze_skill_gap(user, job):
    """Analyze skill gaps and provide learning recommendations"""
    
    user_skills = set(skill.lower() for skill in (user.skills or []))
    job_skills = set(skill.lower() for skill in job.skills)
    
    # Calculate skill match
    matching_skills = user_skills.intersection(job_skills)
    missing_skills = job_skills - user_skills
    
    # Use advanced skill matching
    skill_match_score = calculate_skill_match_score(list(user_skills), list(job_skills))
    
    # Create skill gap analysis
    analysis = SkillGapAnalysis.objects.create(
        user=user,
        job=job,
        current_skills=list(user_skills),
        required_skills=list(job_skills),
        missing_skills=list(missing_skills),
        skill_match_score=skill_match_score,
        learning_recommendations=[]
    )
    
    # Generate learning paths for missing skills
    for skill in list(missing_skills)[:5]:  # Limit to top 5 missing skills
        learning_path = generate_learning_path(skill)
        LearningPath.objects.create(
            skill_analysis=analysis,
            skill=skill.title(),
            courses=learning_path['courses'],
            estimated_duration=learning_path['duration'],
            priority=learning_path['priority']
        )
    
    return analysis

def generate_learning_path(skill):
    """Generate learning path for a specific skill"""
    
    # Enhanced skill course mapping with more comprehensive data
    
    skill_courses = {
        'python': {
            'courses': [
                {
                    'title': 'Python for Everybody Specialization',
                    'provider': 'Coursera',
                    'duration': '8 months',
                    'rating': 4.8,
                    'url': 'https://coursera.org/python'
                },
                {
                    'title': 'Complete Python Developer Bootcamp',
                    'provider': 'Udemy',
                    'duration': '30 hours',
                    'rating': 4.6,
                    'url': 'https://udemy.com/python'
                },
                {
                    'title': 'Python for Data Science',
                    'provider': 'edX',
                    'duration': '10 weeks',
                    'rating': 4.5,
                    'url': 'https://edx.org/python-data-science'
                }
            ],
            'duration': '2-3 months',
            'priority': 1
        },
        'react': {
            'courses': [
                {
                    'title': 'React - The Complete Guide 2024',
                    'provider': 'Udemy',
                    'duration': '52 hours',
                    'rating': 4.7,
                    'url': 'https://udemy.com/react'
                },
                {
                    'title': 'Full-Stack Web Development with React',
                    'provider': 'Coursera',
                    'duration': '6 months',
                    'rating': 4.6,
                    'url': 'https://coursera.org/react'
                },
                {
                    'title': 'React Hooks and Context',
                    'provider': 'Pluralsight',
                    'duration': '4 hours',
                    'rating': 4.4,
                    'url': 'https://pluralsight.com/react-hooks'
                }
            ],
            'duration': '1-2 months',
            'priority': 1
        },
        'machine learning': {
            'courses': [
                {
                    'title': 'Machine Learning Specialization',
                    'provider': 'Coursera',
                    'duration': '3 months',
                    'rating': 4.9,
                    'url': 'https://coursera.org/ml'
                },
                {
                    'title': 'Machine Learning A-Z: Python & R',
                    'provider': 'Udemy',
                    'duration': '50 hours',
                    'rating': 4.6,
                    'url': 'https://udemy.com/ml'
                },
                {
                    'title': 'Introduction to Machine Learning',
                    'provider': 'MIT OpenCourseWare',
                    'duration': '12 weeks',
                    'rating': 4.8,
                    'url': 'https://ocw.mit.edu/ml'
                }
            ],
            'duration': '3-4 months',
            'priority': 2
        },
        'javascript': {
            'courses': [
                {
                    'title': 'The Complete JavaScript Course 2024',
                    'provider': 'Udemy',
                    'duration': '69 hours',
                    'rating': 4.7,
                    'url': 'https://udemy.com/javascript'
                },
                {
                    'title': 'JavaScript Algorithms and Data Structures',
                    'provider': 'freeCodeCamp',
                    'duration': '300 hours',
                    'rating': 4.8,
                    'url': 'https://freecodecamp.org/javascript'
                }
            ],
            'duration': '2-3 months',
            'priority': 1
        },
        'aws': {
            'courses': [
                {
                    'title': 'AWS Certified Solutions Architect',
                    'provider': 'A Cloud Guru',
                    'duration': '25 hours',
                    'rating': 4.6,
                    'url': 'https://acloudguru.com/aws-architect'
                },
                {
                    'title': 'AWS Fundamentals Specialization',
                    'provider': 'Coursera',
                    'duration': '4 months',
                    'rating': 4.5,
                    'url': 'https://coursera.org/aws'
                }
            ],
            'duration': '2-4 months',
            'priority': 2
        },
        'docker': {
            'courses': [
                {
                    'title': 'Docker Mastery: Complete Toolset',
                    'provider': 'Udemy',
                    'duration': '19 hours',
                    'rating': 4.6,
                    'url': 'https://udemy.com/docker'
                },
                {
                    'title': 'Introduction to Containers and Docker',
                    'provider': 'edX',
                    'duration': '4 weeks',
                    'rating': 4.4,
                    'url': 'https://edx.org/docker'
                }
            ],
            'duration': '1-2 months',
            'priority': 2
        }
    }
    
    return skill_courses.get(skill.lower(), {
        'courses': [
            {
                'title': f'Complete {skill.title()} Course',
                'provider': 'Online Learning Platform',
                'duration': '4-8 weeks',
                'rating': 4.2,
                'url': f'https://search.com/courses/{skill.lower()}'
            },
            {
                'title': f'{skill.title()} Fundamentals',
                'provider': 'Tech Academy',
                'duration': '2-4 weeks',
                'rating': 4.0,
                'url': f'https://academy.com/{skill.lower()}'
            }
        ],
        'duration': '1-3 months',
        'priority': 3
    })

def generate_template_cover_letter(user, job, tone):
    """Fallback template-based cover letter generation"""
    
    return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job.title} position at {job.company}. With my background in {user.experience_level} level experience and skills in {', '.join(user.skills[:3]) if user.skills else 'various technologies'}, I am excited about the opportunity to contribute to your team.

In my previous roles, I have developed expertise in areas that align well with your requirements, including {', '.join(job.skills[:3])}. I am particularly drawn to {job.company} because of your reputation for innovation and excellence in the industry.

I would welcome the opportunity to discuss how my skills and enthusiasm can contribute to your team's success. Thank you for considering my application, and I look forward to hearing from you.

Best regards,
{user.first_name} {user.last_name}
{user.email}"""

def generate_template_cold_email(user, job, recruiter_email):
    """Fallback template-based cold email generation"""
    
    return f"""Subject: Experienced {user.experience_level} Level Professional Interested in {job.title} Role

Hi there,

I hope this email finds you well. I came across the {job.title} position at {job.company} and was immediately interested in the opportunity.

With my {user.experience_level} level experience and skills in {', '.join(user.skills[:3]) if user.skills else 'various technologies'}, I believe I would be a strong fit for this role. I'm particularly excited about the chance to work with {job.company} and contribute to your team's success.

I would love to learn more about this opportunity and discuss how my background aligns with your needs. Would you be available for a brief conversation this week?

Best regards,
{user.first_name} {user.last_name}
{user.email}
{user.phone if hasattr(user, 'phone') else ''}"""