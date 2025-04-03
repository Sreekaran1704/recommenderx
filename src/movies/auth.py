import jwt
import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class ClerkJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return None  # No authentication credentials

        token = auth_header.split(' ')[1]

        try:
            # For Clerk, we should verify the token with Clerk's API
            # The correct endpoint for Clerk API v1
            response = requests.post(
                "https://api.clerk.com/v1/tokens/verify",
                headers={
                    "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
                    "Content-Type": "application/json"
                },
                json={"token": token}
            )
            
            if response.status_code != 200:
                print(f"Token verification failed: {response.status_code} - {response.text}")
                raise AuthenticationFailed("Invalid token")
            
            session_data = response.json()
            user_id = session_data.get("sub")  # JWT standard claim for subject
            
            if not user_id:
                raise AuthenticationFailed("Invalid session")
            
            # Fetch user details from Clerk
            user_response = requests.get(
                f"https://api.clerk.com/v1/users/{user_id}",
                headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"}
            )
            
            if user_response.status_code != 200:
                print(f"User fetch failed: {user_response.status_code} - {user_response.text}")
                raise AuthenticationFailed("User not found in Clerk")
            
            user_data = user_response.json()
            return (user_data, None)  # User authenticated
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            raise AuthenticationFailed(f"Authentication failed: {str(e)}")