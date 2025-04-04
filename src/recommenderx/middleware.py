from django.utils.deprecation import MiddlewareMixin

class ClerkAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Get all cookies for debugging
        all_cookies = request.COOKIES
        print(f"All cookies: {all_cookies.keys()}")
        
        # Get Clerk token from cookies or headers
        clerk_token = (
            request.COOKIES.get('clerk_token') or
            request.COOKIES.get('__clerk_db_jwt') or
            request.COOKIES.get('__session') or
            request.headers.get('Authorization', '').replace('Bearer ', '')
        )
        
        # Add debug logging
        if clerk_token:
            token_source = 'unknown'
            if 'clerk_token' in request.COOKIES:
                token_source = 'clerk_token cookie'
            elif '__clerk_db_jwt' in request.COOKIES:
                token_source = '__clerk_db_jwt cookie'
            elif '__session' in request.COOKIES:
                token_source = '__session cookie'
            elif 'Authorization' in request.headers:
                token_source = 'Authorization header'
            
            print(f"Found token from {token_source}: {clerk_token[:10]}...")
            # Check if token starts with expected JWT format
            if clerk_token.startswith('eyJ'):
                print("Token appears to be a valid JWT format")
            else:
                print("Warning: Token does not appear to be in JWT format")
        else:
            print("No authentication token found")
        
        # Store token in request for easy access in views
        request.clerk_token = clerk_token
        
        # Check if user is authenticated
        request.is_authenticated = bool(clerk_token)
        
        return None