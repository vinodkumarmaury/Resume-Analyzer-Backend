from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from .models import Interview
from .serializers import InterviewSerializer, InterviewCreateSerializer

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
def update_interview_status(request, interview_id):
    """Update interview status"""
    try:
        user = request.user
        if user.role == 'recruiter':
            interview = Interview.objects.get(id=interview_id, recruiter=user)
        else:
            interview = Interview.objects.get(id=interview_id, candidate=user)
        
        new_status = request.data.get('status')
        if new_status not in dict(Interview.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interview.status = new_status
        
        # Update feedback and rating if provided (recruiter only)
        if user.role == 'recruiter':
            if 'feedback' in request.data:
                interview.feedback = request.data['feedback']
            if 'rating' in request.data:
                interview.rating = request.data['rating']
        
        interview.save()
        
        serializer = InterviewSerializer(interview)
        return Response(serializer.data)
        
    except Interview.DoesNotExist:
        return Response(
            {"error": "Interview not found or you don't have permission"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": "Failed to update interview status", "detail": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
