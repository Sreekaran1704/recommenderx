import os
import clerk
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.conf import settings
from django.contrib.auth.models import User
from .models import UserProfile
from rest_framework.permissions import IsAuthenticated
from movies.auth import ClerkJWTAuthentication

# Initialize Clerk client
clerk.api_key = settings.CLERK_SECRET_KEY

class UserCreateView(APIView):
    permission_classes = []  # No authentication required for user creation
    
    def post(self, request):
        try:
            # Extract user data from request
            email = request.data.get('email')
            password = request.data.get('password')
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')
            username = request.data.get('username', '')

            print(f"Creating user with email: {email}")
            print(f"Using Clerk API key: {settings.CLERK_SECRET_KEY[:5]}...")
            
            # Validate required fields
            if not email or not password:
                return Response(
                    {"error": "Email and password are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create user in Clerk - using the correct format
            clerk_user = clerk.users.create(
                email_addresses=[{"email_address": email}],
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            django_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create user profile linking Django user to Clerk user
            UserProfile.objects.create(
                user=django_user,
                clerk_user_id=clerk_user.id
            )
            
            return Response(
                {"message": "User created successfully", "user_id": clerk_user.id, "django_user_id": django_user.id}, 
                status=status.HTTP_201_CREATED
            )
            
        except clerk.errors.ClerkError as e:
            # Log the detailed error for debugging
            print(f"Clerk error: {str(e)}")
            return Response(
                {"error": "Failed to create user", "details": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Handle other exceptions
            print(f"Unexpected error: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserProfileView(APIView):
    authentication_classes = [ClerkJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get the Clerk user ID from the authenticated request
            clerk_user_id = request.user.get('id')
            
            # Find the corresponding Django user
            user_profile = UserProfile.objects.get(clerk_user_id=clerk_user_id)
            
            return Response({
                "id": user_profile.user.id,
                "username": user_profile.user.username,
                "email": user_profile.user.email,
                "first_name": user_profile.user.first_name,
                "last_name": user_profile.user.last_name,
                "clerk_user_id": user_profile.clerk_user_id
            })
            
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)