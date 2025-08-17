from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from jobs.models import Job
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample jobs for testing'

    def handle(self, *args, **options):
        # Create a recruiter user if doesn't exist
        recruiter, created = User.objects.get_or_create(
            username='recruiter@example.com',
            defaults={
                'email': 'recruiter@example.com',
                'first_name': 'Test',
                'last_name': 'Recruiter',
                'role': 'recruiter'
            }
        )
        
        if created:
            recruiter.set_password('Test@123')
            recruiter.save()
            self.stdout.write(f'Created recruiter user: {recruiter.username}')

        # Sample jobs
        sample_jobs = [
            {
                'title': 'Senior Python Developer',
                'company': 'TechCorp Inc',
                'location': 'Remote',
                'job_type': 'full-time',
                'salary_min': 80000,
                'salary_max': 120000,
                'description': 'Looking for experienced Python developers with Django experience.',
                'skills': ['Python', 'Django', 'PostgreSQL', 'AWS'],
                'requirements': ['5+ years Python experience', 'Django framework', 'REST APIs'],
            },
            {
                'title': 'Frontend React Developer',
                'company': 'WebDev Solutions',
                'location': 'New York, NY',
                'job_type': 'full-time',
                'salary_min': 70000,
                'salary_max': 100000,
                'description': 'Join our team to build amazing user interfaces with React.',
                'skills': ['React', 'JavaScript', 'CSS', 'TypeScript'],
                'requirements': ['3+ years React experience', 'Modern JavaScript', 'Responsive design'],
            },
            {
                'title': 'Full Stack Developer',
                'company': 'StartupXYZ',
                'location': 'San Francisco, CA',
                'job_type': 'full-time',
                'salary_min': 90000,
                'salary_max': 130000,
                'description': 'Full stack developer for fast-growing startup.',
                'skills': ['Node.js', 'React', 'MongoDB', 'Express'],
                'requirements': ['Full stack experience', 'Startup experience preferred', 'Agile methodology'],
            }
        ]

        for job_data in sample_jobs:
            job, created = Job.objects.get_or_create(
                title=job_data['title'],
                company=job_data['company'],
                defaults={
                    **job_data,
                    'posted_by': recruiter,
                    'expires_at': timezone.now() + timedelta(days=30)
                }
            )
            
            if created:
                self.stdout.write(f'Created job: {job.title} at {job.company}')
            else:
                self.stdout.write(f'Job already exists: {job.title} at {job.company}')

        self.stdout.write(self.style.SUCCESS('Sample jobs created successfully!'))