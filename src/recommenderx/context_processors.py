from django.conf import settings

def clerk_settings(request):
    """Make Clerk settings available to all templates."""
    key = settings.CLERK_PUBLISHABLE_KEY
    print(f"Context processor providing Clerk key: {key}")
    return {
        'CLERK_PUBLISHABLE_KEY': key,
    }