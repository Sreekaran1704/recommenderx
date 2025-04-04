from django.http import HttpResponse
from django.shortcuts import render, redirect
import requests
import json
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def home_page_view(request, *args, **kwargs):
    return render(request, 'home.html', {
        'CLERK_PUBLISHABLE_KEY': settings.CLERK_PUBLISHABLE_KEY,
    })

def movie_list_view(request):

    search_query = request.GET.get('q', '')
    genre_filter = request.GET.get('genre', '')
    sort_by = request.GET.get('sort', 'title')  # Default sort by title
    
    # Make API request to our backend
    if search_query:
        response = requests.get(f'http://localhost:8000/api/movies/search/?q={search_query}')
        data = response.json()
        movies = data.get('results', [])
    elif genre_filter:
        response = requests.get(f'http://localhost:8000/api/movies/genre/{genre_filter}/')
        data = response.json()
        movies = data.get('movies', [])
    else:
        response = requests.get('http://localhost:8000/api/movies/')
        movies = response.json()
    
    # Sort movies based on user preference
    if sort_by == 'title':
        movies = sorted(movies, key=lambda x: x.get('title', '').lower())
    elif sort_by == 'rating':
        # Assuming movies have an average_rating field
        movies = sorted(movies, key=lambda x: x.get('average_rating', 0), reverse=True)
    elif sort_by == 'release_date':
        # Sort by release date (newest first)
        movies = sorted(movies, key=lambda x: x.get('release_date', ''), reverse=True)
    
    # Get genres for filter dropdown
    genres_response = requests.get('http://localhost:8000/api/movies/genres/')
    genres = genres_response.json().get('genres', [])
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(movies, 12)  # Show 12 movies per page
    
    try:
        movies_page = paginator.page(page)
    except PageNotAnInteger:
        movies_page = paginator.page(1)
    except EmptyPage:
        movies_page = paginator.page(paginator.num_pages)
    
    return render(request, 'movies/movie_list.html', {
        'movies': movies_page,
        'genres': genres,
        'current_genre': genre_filter,
        'search_query': search_query,
        'sort_by': sort_by,
        'page_obj': movies_page,  # For pagination template
    })

def movie_detail_view(request, movie_id):

    # Get the movie details
    response = requests.get(f'http://localhost:8000/api/movies/{movie_id}/')
    movie = response.json()
    
    # Ensure movie has an id field
    if 'id' not in movie:
        movie['id'] = movie_id
    
    # Get all cookies for debugging
    all_cookies = request.COOKIES
    print(f"All cookies: {all_cookies.keys()}")
    
    # Try multiple ways to get the Clerk token
    clerk_token = (
        request.COOKIES.get('clerk_token') or
        request.COOKIES.get('__clerk_db_jwt') or
        request.COOKIES.get('__session') or
        request.headers.get('Authorization', '').replace('Bearer ', '')
    )
    
    # Get ratings directly from the database
    try:
        from movies.models import Rating
        import hashlib
        from django.contrib.auth.models import User
        
        # Get all ratings for this movie
        all_ratings = Rating.objects.filter(movie_id=movie_id)
        
        # Calculate average rating
        if all_ratings.exists():
            avg_rating = sum(r.rating for r in all_ratings) / all_ratings.count()
            ratings_count = all_ratings.count()
        else:
            avg_rating = 0
            ratings_count = 0
        
        # Format ratings for the template
        ratings_list = []
        for r in all_ratings:
            ratings_list.append({
                'id': r.id,
                'user_id': r.user_id,
                'movie_id': r.movie_id,
                'rating': r.rating,
                'review': r.review,
                'user_name': r.user_name or f"User {r.user_id}"
            })
        
        # Set movie rating data
        movie['average_rating'] = avg_rating
        movie['ratings_count'] = ratings_count
        movie['ratings'] = ratings_list
        
        # Check if current user has rated this movie
        user_rating = None
        if clerk_token:
            # Get the Django user ID for this clerk token
            hash_object = hashlib.md5(clerk_token.encode())
            username = f"clerk_{hash_object.hexdigest()[:8]}"
            
            try:
                user = User.objects.get(username=username)
                user_id = user.id
                
                # Get the user's rating directly from the database
                user_rating_obj = Rating.objects.filter(
                    user_id=user_id,
                    movie_id=movie_id
                ).first()
                
                if user_rating_obj:
                    user_rating = {
                        'id': user_rating_obj.id,
                        'user_id': user_id,
                        'movie_id': int(movie_id),
                        'rating': user_rating_obj.rating,
                        'review': user_rating_obj.review,
                        'user_name': username
                    }
                    print(f"Found user rating in database: {user_rating}")
            except User.DoesNotExist:
                print(f"User with username {username} not found")
        
        movie['user_rating'] = user_rating
        
    except Exception as e:
        print(f"Error getting ratings from database: {str(e)}")
        movie['average_rating'] = 0
        movie['ratings_count'] = 0
        movie['ratings'] = []
        movie['user_rating'] = None
    
    # Check if user is authenticated for template
    is_authenticated = bool(clerk_token)
    
    # Debug the final movie object
    print(f"Final movie object has user_rating: {movie.get('user_rating') is not None}")
    if movie.get('user_rating'):
        print(f"User rating value in final object: {movie['user_rating'].get('rating')}")
    
    # Add a context variable specifically for the user's rating
    context = {
        'movie': movie,
        'CLERK_PUBLISHABLE_KEY': settings.CLERK_PUBLISHABLE_KEY,
        'is_authenticated': is_authenticated,
        'user_rating': movie.get('user_rating'),
        'has_ratings': len(movie.get('ratings', [])) > 0,
    }
    
    return render(request, 'movies/movie_detail.html', context)

def recommendations_view(request):
    # In a real app, this would use the authenticated user
    # For now, we'll just fetch general recommendations
    try:
        response = requests.get('http://localhost:8000/api/movies/recommendations/')
        recommended_movies = response.json()
    except:
        recommended_movies = []
    
    return render(request, 'movies/recommendations.html', {
        'movies': recommended_movies
    })

def watchlist_view(request):
    # In a real app, this would use the authenticated user
    # For now, we'll just show a message
    return render(request, 'movies/watchlist.html', {
        'movies': []
    })

def add_to_watchlist_view(request):
    if request.method == 'POST':
        movie_id = request.POST.get('movie_id')
        # In a real app, this would add the movie to the user's watchlist
        # For now, we'll just redirect back
        return redirect(f'/movies/{movie_id}/')
    return redirect('/movies/')

def login_view(request):
    # Check if there's a redirect URL in the session
    redirect_url = request.session.get('redirect_after_login', '/')
    
    # Pass the Clerk publishable key and redirect URL to the template
    return render(request, 'users/login.html', {
        'CLERK_PUBLISHABLE_KEY': settings.CLERK_PUBLISHABLE_KEY,
        'redirect_url': redirect_url
    })

def signup_view(request):
    # Pass the Clerk publishable key to the template
    return render(request, 'users/signup.html', {
        'CLERK_PUBLISHABLE_KEY': settings.CLERK_PUBLISHABLE_KEY
    })

def logout_view(request):
    return redirect('/')

def profile_view(request):
    # Get the Clerk token from the request headers or cookies
    clerk_token = request.COOKIES.get('clerk_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not clerk_token:
        return redirect('/login/')
    
    # Get user profile data using the Clerk token
    try:
        headers = {'Authorization': f'Bearer {clerk_token}'}
        response = requests.get('http://localhost:8000/api/users/profile/', headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Get user's ratings
            user_id = user_data.get('id')
            ratings_response = requests.get(
                f'http://localhost:8000/api/ratings/user/{user_id}/',
                headers=headers
            )
            
            if ratings_response.status_code == 200:
                ratings_data = ratings_response.json()
                user_data['ratings'] = ratings_data.get('ratings', [])
            else:
                user_data['ratings'] = []
            
            return render(request, 'users/profile.html', {'user': user_data})
        else:
            return redirect('/login/')
            
    except Exception as e:
        return redirect('/login/')

def add_rating_view(request):
    if request.method == 'POST':
        # Check if this is a form submission or API request
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                movie_id = data.get('movie_id')
                rating_value = data.get('rating')
                review = data.get('review', '')
            except json.JSONDecodeError:
                print("Error decoding JSON data")
                return HttpResponse(status=400)
        else:
            # Form submission
            movie_id = request.POST.get('movie_id')
            rating_value = request.POST.get('rating')
            review = request.POST.get('review', '')

        print(f"Received rating request for movie_id: {movie_id}, rating: {rating_value}")

        # Get the Clerk token
        clerk_token = (
            request.COOKIES.get('clerk_token') or
            request.COOKIES.get('__clerk_db_jwt') or
            request.COOKIES.get('__session') or
            request.headers.get('Authorization', '').replace('Bearer ', '')
        )
        
        print(f"Token found: {bool(clerk_token)}")
        if clerk_token:
            print(f"Token starts with: {clerk_token[:10]}...")
        
        # Add the rating directly to the database
        try:
            print("Attempting to create/update rating in database")
            
            # Get or create a Django user for this Clerk user
            import hashlib
            from django.contrib.auth.models import User
            
            hash_object = hashlib.md5(clerk_token.encode())
            username = f"clerk_{hash_object.hexdigest()[:8]}"
            
            user, created = User.objects.get_or_create(username=username)
            print(f"Using auth user ID: {user.id} (created: {created})")
            
            # Now create or update the rating directly in the database
            from movies.models import Rating
            
            rating_obj, created = Rating.objects.update_or_create(
                user_id=user.id,
                movie_id=movie_id,
                defaults={
                    'rating': int(rating_value),
                    'review': review,
                    'user_name': username
                }
            )
            
            if created:
                print(f"Created new rating (ID: {rating_obj.id})")
                messages.success(request, "Rating added successfully!")
            else:
                print(f"Updated existing rating (ID: {rating_obj.id})")
                messages.success(request, "Rating updated successfully!")
                
            # If this was an API request, return a JSON response
            if request.content_type == 'application/json':
                return JsonResponse({'success': True, 'message': 'Rating saved'})
                
        except Exception as e:
            print(f"Error adding rating: {str(e)}")
            messages.error(request, "Error adding rating. Please try again.")
            
            # If this was an API request, return an error response
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
        
        return redirect(f'/movies/{movie_id}/')
    
    return redirect('/movies/')
