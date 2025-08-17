from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Interview
from .serializers import InterviewSerializer, InterviewCreateSerializer
from jobs.models import Job
import logging

logger = logging.getLogger(__name__)

class InterviewListCreateView(generics.ListCreateAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'recruiter':
            return Interview.objects.filter(recruiter=user)
        else:
            return Interview.objects.filter(candidate=user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return InterviewCreateSerializer
        return InterviewSerializer
    
    def perform_create(self, serializer):
        serializer.save(recruiter=self.request.user)

class InterviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'recruiter':
            return Interview.objects.filter(recruiter=user)
        else:
            return Interview.objects.filter(candidate=user)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_interview(request):
    """Schedule an interview for a job and candidate"""
    
    job_id = request.data.get('job_id')
    candidate_id = request.data.get('candidate_id')
    scheduled_date = request.data.get('scheduled_date')
    interview_type = request.data.get('interview_type', 'video')
    location = request.data.get('location', '')
    notes = request.data.get('notes', '')
    duration_minutes = request.data.get('duration_minutes', 60)
    
    if not job_id or not candidate_id or not scheduled_date:
        return Response(
            {"error": "job_id, candidate_id and scheduled_date are required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Only recruiters can schedule interviews
        if request.user.role != 'recruiter':
            return Response(
                {"error": "Only recruiters can schedule interviews"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        job = Job.objects.get(id=job_id, posted_by=request.user)
        from authentication.models import User
        candidate = User.objects.get(id=candidate_id, role='candidate')
        
        # Parse and validate date
        try:
            interview_datetime = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
            if interview_datetime < timezone.now():
                return Response(
                    {"error": "Interview date cannot be in the past"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing interview
        existing_interview = Interview.objects.filter(
            job=job, 
            candidate=candidate,
            status='scheduled'
        ).first()
        if existing_interview:
            return Response(
                {"error": "Interview already scheduled for this job and candidate"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create interview
        interview = Interview.objects.create(
            job=job,
            candidate=candidate,
            recruiter=request.user,
            scheduled_date=interview_datetime,
            interview_type=interview_type,
            location=location,
            notes=notes,
            duration_minutes=duration_minutes
        )
        
        serializer = InterviewSerializer(interview)
        
        return Response({
            "success": True,
            "message": "Interview scheduled successfully",
            "interview": serializer.data,
            "next_steps": [
                "Candidate will be notified of the scheduled interview",
                "Meeting details have been saved",
                "You can update or cancel the interview if needed"
            ]
        }, status=status.HTTP_201_CREATED)
        
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found or you don't have permission"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except User.DoesNotExist:
        return Response(
            {"error": "Candidate not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error scheduling interview: {str(e)}")
        return Response(
            {"error": "Failed to schedule interview", "detail": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_interviews(request):
    """Get interviews for the current user with enhanced filtering"""
    
    try:
        if request.user.role == 'recruiter':
            interviews = Interview.objects.filter(recruiter=request.user)
        elif request.user.role == 'candidate':
            interviews = Interview.objects.filter(candidate=request.user)
        else:
            return Response(
                {"error": "Invalid user role"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            interviews = interviews.filter(status=status_filter)
        
        # Filter by date range if provided
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                interviews = interviews.filter(scheduled_date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                interviews = interviews.filter(scheduled_date__lte=date_to_obj)
            except ValueError:
                pass
        
        # Order by date
        interviews = interviews.order_by('-scheduled_date')
        
        serializer = InterviewSerializer(interviews, many=True)
        
        # Add summary stats
        total_interviews = interviews.count()
        upcoming_interviews = interviews.filter(
            scheduled_date__gte=timezone.now(),
            status='scheduled'
        ).count()
        completed_interviews = interviews.filter(status='completed').count()
        
        return Response({
            "interviews": serializer.data,
            "summary": {
                "total": total_interviews,
                "upcoming": upcoming_interviews,
                "completed": completed_interviews,
                "cancelled": interviews.filter(status='cancelled').count()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting interviews: {str(e)}")
        return Response(
            {"error": "Failed to fetch interviews", "detail": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_interview_status(request, interview_id):
    """Update interview status with enhanced validation and feedback"""
    try:
        user = request.user
        if user.role == 'recruiter':
            interview = Interview.objects.get(id=interview_id, recruiter=user)
        else:
            interview = Interview.objects.get(id=interview_id, candidate=user)
        
        new_status = request.data.get('status')
        if new_status not in dict(Interview.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status. Choose from: " + ", ".join([choice[0] for choice in Interview.STATUS_CHOICES])}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status transitions
        if interview.status == 'completed' and new_status != 'completed':
            return Response(
                {"error": "Cannot change status of a completed interview"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interview.status = new_status
        
        # Update feedback and rating if provided (recruiter only)
        if user.role == 'recruiter':
            if 'feedback' in request.data:
                interview.feedback = request.data['feedback']
            if 'rating' in request.data:
                try:
                    rating = int(request.data['rating'])
                    if 1 <= rating <= 5:
                        interview.rating = rating
                    else:
                        return Response(
                            {"error": "Rating must be between 1 and 5"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except (ValueError, TypeError):
                    return Response(
                        {"error": "Rating must be a valid integer"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        interview.save()
        
        serializer = InterviewSerializer(interview)
        return Response({
            "success": True,
            "message": f"Interview status updated to {new_status}",
            "interview": serializer.data
        })
        
    except Interview.DoesNotExist:
        return Response(
            {"error": "Interview not found or you don't have permission"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error updating interview status: {str(e)}")
        return Response(
            {"error": "Failed to update interview status", "detail": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reschedule_interview(request, interview_id):
    """Reschedule an interview"""
    
    try:
        user = request.user
        if user.role == 'recruiter':
            interview = Interview.objects.get(id=interview_id, recruiter=user)
        elif user.role == 'candidate':
            interview = Interview.objects.get(id=interview_id, candidate=user)
        else:
            return Response(
                {"error": "Invalid user role"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow rescheduling of scheduled interviews
        if interview.status != 'scheduled':
            return Response(
                {"error": "Can only reschedule scheduled interviews"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_date = request.data.get('scheduled_date')
        if not new_date:
            return Response(
                {"error": "scheduled_date is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            interview_datetime = datetime.fromisoformat(new_date.replace('Z', '+00:00'))
            if interview_datetime < timezone.now():
                return Response(
                    {"error": "Interview date cannot be in the past"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Invalid date format"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interview.scheduled_date = interview_datetime
        
        # Update other fields if provided
        if 'interview_type' in request.data:
            interview.interview_type = request.data['interview_type']
        if 'location' in request.data:
            interview.location = request.data['location']
        if 'notes' in request.data:
            interview.notes = request.data['notes']
        if 'duration_minutes' in request.data:
            interview.duration_minutes = request.data['duration_minutes']
        
        interview.save()
        
        serializer = InterviewSerializer(interview)
        return Response({
            "success": True,
            "message": "Interview rescheduled successfully",
            "interview": serializer.data
        })
        
    except Interview.DoesNotExist:
        return Response(
            {"error": "Interview not found or you don't have permission"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error rescheduling interview: {str(e)}")
        return Response(
            {"error": "Failed to reschedule interview", "detail": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
