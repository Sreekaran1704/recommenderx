def get_clerk_token_from_request(request):
    """
    Extract the Clerk token from request cookies or headers.
    
    Args:
        request: The Django request object
        
    Returns:
        str: The Clerk token or None if not found
    """
    return (
        request.COOKIES.get('clerk_token') or
        request.COOKIES.get('__clerk_db_jwt') or
        request.COOKIES.get('__session') or
        request.headers.get('Authorization', '').replace('Bearer ', '')
    )