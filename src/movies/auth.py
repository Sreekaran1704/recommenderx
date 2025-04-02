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
            # Decode the JWT using Clerk's secret key
            payload = jwt.decode(token, settings.CLERK_SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("sub")

            if not user_id:
                raise AuthenticationFailed("Invalid token")

            # Fetch user details from Clerk
            response = requests.get(f"https://api.clerk.dev/v1/users/{user_id}", 
                                    headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"})

            if response.status_code != 200:
                raise AuthenticationFailed("User not found in Clerk")

            user_data = response.json()
            return (user_data, None)  # User authenticated

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")
