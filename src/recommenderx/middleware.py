from django.utils.deprecation import MiddlewareMixin

class ClerkAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Get Clerk token from cookies or headers
        clerk_token = request.COOKIES.get('__clerk_session') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        # Store token in request for easy access in views
        request.clerk_token = clerk_token
        
        # Check if user is authenticated
        request.is_authenticated = bool(clerk_token)
        
        return None