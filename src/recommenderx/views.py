from django.http import HttpResponse
from django.shortcuts import render, redirect
import requests  # Make sure this is imported at the top level
import json
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def home_page_view(request):
    """Home page view showing featured and recommended movies."""
    try:
        from movies.models import Movie
        
        # Get total count for debugging
        total_count = Movie.objects.count()
        print(f"Total movies in database: {total_count}")
        
        # Just get any movies to display
        all_movies = list(Movie.objects.all()[:20])
        
        if all_movies:
            featured_movie = all_movies[0] if all_movies else None
            recommended_movies = all_movies[1:5] if len(all_movies) > 1 else []
            popular_movies = all_movies[5:13] if len(all_movies) > 5 else []
            
            print(f"Featured: {featured_movie.title if featured_movie else 'None'}")
            print(f"Recommended: {len(recommended_movies)} movies")
            print(f"Popular: {len(popular_movies)} movies")
        else:
            print("No movies found in database")
            featured_movie = None
            recommended_movies = []
            popular_movies = []
        
    except Exception as e:
        print(f"Error fetching movies for homepage: {str(e)}")
        featured_movie = None
        recommended_movies = []
        popular_movies = []
    
    return render(request, 'home.html', {
        'featured_movie': featured_movie,
        'recommended_movies': recommended_movies,
        'popular_movies': popular_movies,
        'CLERK_PUBLISHABLE_KEY': settings.CLERK_PUBLISHABLE_KEY
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
    
    # Add rating information to each movie
    try:
        from movies.models import Rating
        
        for movie in movies:
            # Get all ratings for this movie
            ratings = Rating.objects.filter(movie_id=movie['id'])
            
            if ratings.exists():
                # Calculate average rating
                avg_rating = sum(r.rating for r in ratings) / ratings.count()
                movie['rating'] = avg_rating
                movie['ratings_count'] = ratings.count()
            else:
                movie['rating'] = 0
                movie['ratings_count'] = 0
    except Exception as e:
        print(f"Error adding ratings to movies: {str(e)}")
    
    # Sort movies based on user preference
    if sort_by == 'title':
        movies = sorted(movies, key=lambda x: x.get('title', '').lower())
    elif sort_by == 'rating':
        # Use the 'rating' field we added earlier
        movies = sorted(movies, key=lambda x: x.get('rating', 0), reverse=True)
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
    
    # Check if there's an LLM recommendation request
    llm_recommendation = None
    if request.GET.get('get_recommendation') == 'true':
        try:
            # Remove this import as it's already imported at the top
            # import requests  <- Remove this line
            
            # Prepare movie information for the prompt
            movie_title = movie.get('title', 'this movie')
            movie_genre = movie.get('genre', '')
            movie_description = movie.get('description', '')
            movie_rating = movie.get('average_rating', 0)
            
            # Construct a prompt for the LLM
            prompt = f"""Based on the following information about '{movie_title}'
            is this movie worth watching? Give me the review whether this movie is worth watching in a unhinged manner if the movie is good praise it like a die hard fan but if the movie is bad trash it into grounds basically review like a toxic and stric reviewer"""
            
            # Make a request to Groq API with Llama 3
            groq_api_key = settings.GROQ_API_KEY
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                response_data = response.json()
                llm_recommendation = response_data['choices'][0]['message']['content'].strip()
                print(f"Generated LLM recommendation for {movie_title}")
            else:
                print(f"Error from Groq API: {response.status_code}, {response.text}")
                llm_recommendation = "Unable to generate a recommendation at this time. Please try again later."
                
        except Exception as e:
            print(f"Error generating LLM recommendation: {str(e)}")
            llm_recommendation = "Unable to generate a recommendation at this time. Please try again later."
    
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
        'llm_recommendation': llm_recommendation,  # Add the LLM recommendation to the context
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
    # Get the Clerk token
    clerk_token = (
        request.COOKIES.get('clerk_token') or
        request.COOKIES.get('__clerk_db_jwt') or
        request.COOKIES.get('__session') or
        request.headers.get('Authorization', '').replace('Bearer ', '')
    )
    
    if not clerk_token:
        # Redirect to login if not authenticated
        request.session['redirect_after_login'] = '/watchlist/'
        return redirect('/login/')
    
    try:
        # Get the Django user for this Clerk user
        import hashlib
        from django.contrib.auth.models import User
        
        hash_object = hashlib.md5(clerk_token.encode())
        username = f"clerk_{hash_object.hexdigest()[:8]}"
        
        user = User.objects.get(username=username)
        
        # Get the user's watchlist
        from movies.models import Watchlist
        watchlist_items = Watchlist.objects.filter(user_id=user.id)
        
        # Format the watchlist items for the template
        movies = []
        for item in watchlist_items:
            movies.append({
                'id': item.movie.id,
                'title': item.movie.title,
                'genre': item.movie.genre,
                'description': item.movie.description,
                'poster_url': item.movie.poster_url,
                'watchlist_id': item.id,  # For removal functionality
            })
        
        return render(request, 'movies/watchlist.html', {
            'movies': movies,
            'is_authenticated': True,
        })
        
    except Exception as e:
        print(f"Error getting watchlist: {str(e)}")
        messages.error(request, "Error retrieving your watchlist.")
        return render(request, 'movies/watchlist.html', {
            'movies': [],
            'is_authenticated': True,
            'error': str(e)
        })

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

def add_to_watchlist_view(request):
    if request.method == 'POST':
        movie_id = request.POST.get('movie_id')
        
        # Get the Clerk token
        clerk_token = (
            request.COOKIES.get('clerk_token') or
            request.COOKIES.get('__clerk_db_jwt') or
            request.COOKIES.get('__session') or
            request.headers.get('Authorization', '').replace('Bearer ', '')
        )
        
        if clerk_token:
            try:
                # Get or create a Django user for this Clerk user
                import hashlib
                from django.contrib.auth.models import User
                from movies.models import Movie, Watchlist
                
                hash_object = hashlib.md5(clerk_token.encode())
                username = f"clerk_{hash_object.hexdigest()[:8]}"
                
                user, created = User.objects.get_or_create(username=username)
                
                # Get the movie object
                movie = Movie.objects.get(id=movie_id)
                
                # Check if the movie is already in the watchlist
                existing = Watchlist.objects.filter(user_id=user.id, movie=movie).exists()
                
                if not existing:
                    # Create watchlist entry
                    watchlist_item = Watchlist(
                        user_id=user.id,
                        movie=movie,
                        title=movie.title,
                        poster_url=movie.poster_url
                    )
                    watchlist_item.save()
                    
                    messages.success(request, "Movie added to your watchlist!")
                else:
                    messages.info(request, "This movie is already in your watchlist.")
                    
            except Movie.DoesNotExist:
                messages.error(request, "Movie not found.")
            except Exception as e:
                print(f"Error adding to watchlist: {str(e)}")
                messages.error(request, "Error adding to watchlist. Please try again.")
        else:
            # Redirect to login if not authenticated
            request.session['redirect_after_login'] = f'/movies/{movie_id}/'
            return redirect('/login/')
            
        return redirect(f'/movies/{movie_id}/')
    return redirect('/movies/')

# Add this function after add_to_watchlist_view

def remove_from_watchlist_view(request):
    if request.method == 'POST':
        watchlist_id = request.POST.get('watchlist_id')
        
        # Get the Clerk token
        clerk_token = (
            request.COOKIES.get('clerk_token') or
            request.COOKIES.get('__clerk_db_jwt') or
            request.COOKIES.get('__session') or
            request.headers.get('Authorization', '').replace('Bearer ', '')
        )
        
        if clerk_token:
            try:
                # Get the Django user for this Clerk user
                import hashlib
                from django.contrib.auth.models import User
                from movies.models import Watchlist
                
                hash_object = hashlib.md5(clerk_token.encode())
                username = f"clerk_{hash_object.hexdigest()[:8]}"
                
                user = User.objects.get(username=username)
                
                # Get the watchlist item
                watchlist_item = Watchlist.objects.get(id=watchlist_id, user_id=user.id)
                
                # Delete the watchlist item
                watchlist_item.delete()
                
                messages.success(request, "Movie removed from your watchlist!")
                
            except Watchlist.DoesNotExist:
                messages.error(request, "Watchlist item not found.")
            except Exception as e:
                print(f"Error removing from watchlist: {str(e)}")
                messages.error(request, "Error removing from watchlist. Please try again.")
        else:
            # Redirect to login if not authenticated
            return redirect('/login/')
            
        return redirect('/watchlist/')
    return redirect('/movies/')


# Add this function after your existing views

def search_movies_view(request):
    search_query = request.GET.get('q', '')
    
    if not search_query:
        return redirect('movie_list')

    print(f"Search query: {search_query}")
    # Get the Clerk token 
    # Make API request to our backend search endpoint
    try:
        # Get the Clerk token for authentication
        clerk_token = (
            request.COOKIES.get('clerk_token') or
            request.COOKIES.get('__clerk_db_jwt') or
            request.COOKIES.get('__session') or
            request.headers.get('Authorization', '').replace('Bearer ', '')
        )
        
        # Set up headers for the API request
        headers = {}
        if clerk_token:
            headers['Authorization'] = f'Bearer {clerk_token}'
            
        # Make the request to the API
        api_url = f'http://localhost:8000/api/movies/search/?q={search_query}'
        print(f"Making API request to: {api_url}")
        response = requests.get(
            f'http://localhost:8000/api/movies/search/?q={search_query}',
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check if the response has a 'results' key
            if 'results' in data:
                movies = data['results']
            else:
                # If the API returns a list directly
                movies = data
        else:
            print(f"Search API returned status code: {response.status_code}")
            movies = []
    except Exception as e:
        print(f"Error fetching search results: {str(e)}")
        movies = []

    # Get genres for filter dropdown (handle potential error)
    try:
        genres_response = requests.get('http://localhost:8000/api/movies/genres/')
        if genres_response.status_code == 200:
            genres = genres_response.json().get('genres', [])
        else:
            genres = []
    except Exception as e:
        print(f"Error fetching genres: {str(e)}")
        genres = []    
    
    # Sort movies by title
    movies = sorted(movies, key=lambda x: x.get('title', '').lower())
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(movies, 12)  # Show 12 movies per page
    
    try:
        movies_page = paginator.page(page)
    except PageNotAnInteger:
        movies_page = paginator.page(1)
    except EmptyPage:
        movies_page = paginator.page(paginator.num_pages)
    
    # Render the search results template with all necessary context
    context = {
        'query': search_query,
        'movies': movies_page,
        'genres': genres,
        'current_genre': '',
        'search_query': search_query,
        'sort_by': 'title',
        'page_obj': movies_page,  # For pagination template
        'CLERK_PUBLISHABLE_KEY': settings.CLERK_PUBLISHABLE_KEY
    }
    
    print(f"Rendering template with {len(movies)} movies")
    return render(request, 'movies/search_results.html', context)