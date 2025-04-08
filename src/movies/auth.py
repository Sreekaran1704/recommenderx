import jwt
import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class ClerkJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        # Try to get token from Authorization header
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        # Try to get token from cookies - check multiple possible cookie names
        elif 'clerk_token' in request.COOKIES:
            token = request.COOKIES['clerk_token']
        elif '__clerk_db_jwt' in request.COOKIES:
            token = request.COOKIES['__clerk_db_jwt']
        elif '__session' in request.COOKIES:
            token = request.COOKIES['__session']
        else:
            return None  # No authentication credentials
        
        # Check if token is in JWT format
        if not token.startswith('eyJ'):
            print(f"Token is not in JWT format: {token[:10]}...")
            
            # TEMPORARY FIX: For session tokens (starting with dvb_), 
            # create a simple user object for rating operations
            if token.startswith('dvb_') and ('ratings' in request.path or 'watchlist' in request.path or 'search' in request.path):
                print(f"Using session token for {request.path}")
                # Create a simple user object with the session ID as the user ID
                user = type('ClerkUser', (), {
                    'id': token,  # Use the session token as the user ID
                    'is_authenticated': True,
                    'username': 'session_user',
                    'email': '',
                    'first_name': 'Guest',
                    'last_name': 'User'
                })
                return (user, token)
            return None
            
        try:
            # For Clerk, we should verify the token with Clerk's API
            # The correct endpoint for Clerk API v2
            response = requests.post(
                "https://api.clerk.dev/v1/tokens/verify",
                headers={
                    "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
                    "Content-Type": "application/json"
                },
                json={"token": token}
            )
            
            if response.status_code != 200:
                print(f"Token verification failed: {response.status_code} - {response.text}")
                raise AuthenticationFailed("Invalid token")
                
            # Extract user data from the verified token
            user_data = response.json()
            user_id = user_data.get("sub")
            
            if not user_id:
                raise AuthenticationFailed("Invalid user ID in token")
                
            # Create a simple user object with the ID
            user = type('ClerkUser', (), {
                'id': user_id,
                'is_authenticated': True,
                'username': user_id,
                'email': user_data.get("email", ""),
                'first_name': user_data.get("first_name", ""),
                'last_name': user_data.get("last_name", "")
            })
            
            return (user, token)
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            raise AuthenticationFailed("Invalid token")
    
    def authenticate_header(self, request):
        return 'Bearer'