from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, UserProfile
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        else:
            # If no refresh token provided, just return success
            # The frontend will handle token removal
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_preferences(request):
    """Get or update user preferences"""
    
    if request.method == 'GET':
        # Return user preferences
        user = request.user
        preferences = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "phone": user.phone,
            "location": user.location,
            "experience_level": user.experience_level,
            "bio": user.bio,
            "skills": user.skills,
            "profile_complete": user.profile_complete,
            "preferences": {
                "email_notifications": True,
                "job_alerts": True,
                "newsletter": True,
                "privacy_mode": False,
                "show_profile": True,
                "job_recommendations": True
            },
            "profile": {
                "linkedin_url": user.profile.linkedin_url if hasattr(user, 'profile') else "",
                "github_url": user.profile.github_url if hasattr(user, 'profile') else "",
                "portfolio_url": user.profile.portfolio_url if hasattr(user, 'profile') else "",
                "education": user.profile.education if hasattr(user, 'profile') else [],
                "work_experience": user.profile.work_experience if hasattr(user, 'profile') else [],
                "certifications": user.profile.certifications if hasattr(user, 'profile') else [],
                "languages": user.profile.languages if hasattr(user, 'profile') else []
            }
        }
        return Response(preferences)
    
    elif request.method == 'PUT':
        # Update user preferences
        user = request.user
        data = request.data
        
        try:
            # Update user fields
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'phone' in data:
                user.phone = data['phone']
            if 'location' in data:
                user.location = data['location']
            if 'experience_level' in data:
                user.experience_level = data['experience_level']
            if 'bio' in data:
                user.bio = data['bio']
            if 'skills' in data:
                user.skills = data['skills']
            
            user.save()
            
            # Update profile fields if provided
            if hasattr(user, 'profile'):
                profile = user.profile
                if 'profile' in data:
                    profile_data = data['profile']
                    if 'linkedin_url' in profile_data:
                        profile.linkedin_url = profile_data['linkedin_url']
                    if 'github_url' in profile_data:
                        profile.github_url = profile_data['github_url']
                    if 'portfolio_url' in profile_data:
                        profile.portfolio_url = profile_data['portfolio_url']
                    if 'education' in profile_data:
                        profile.education = profile_data['education']
                    if 'work_experience' in profile_data:
                        profile.work_experience = profile_data['work_experience']
                    if 'certifications' in profile_data:
                        profile.certifications = profile_data['certifications']
                    if 'languages' in profile_data:
                        profile.languages = profile_data['languages']
                    
                    profile.save()
            
            return Response({
                "success": True,
                "message": "Preferences updated successfully",
                "user": UserSerializer(user).data
            })
            
        except Exception as e:
            return Response(
                {"error": "Failed to update preferences", "detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )