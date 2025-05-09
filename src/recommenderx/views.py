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
    from django.db.models import Q
    from django.apps import apps
    
    # Get the Movie model
    Movie = apps.get_model('movies', 'Movie')
    
    search_query = request.GET.get('q', '')
    genre_filter = request.GET.get('genre', '')
    sort_by = request.GET.get('sort', 'title')  # Default sort by title
    
    # Query the database directly instead of making API requests
    if search_query:
        # Search for movies by title or genre
        movies_queryset = Movie.objects.filter(
            Q(title__icontains=search_query) | 
            Q(genre__icontains=search_query)
        )
    elif genre_filter:
        # Filter by genre
        movies_queryset = Movie.objects.filter(genre__icontains=genre_filter)
    else:
        # Get all movies
        movies_queryset = Movie.objects.all()
    
    # Convert queryset to list of dictionaries
    movies = []
    for movie in movies_queryset:
        movies.append({
            "id": movie.id,
            "title": movie.title,
            "genre": movie.genre,
            "poster_url": movie.poster_url,
            "description": movie.description
        })
    
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
    
    # Get genres for filter dropdown directly from database
    genres = list(Movie.objects.values_list('genre', flat=True).distinct())
    genres = sorted(genres)
    
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
    from django.apps import apps
    from django.shortcuts import get_object_or_404
    
    # Get the Movie model
    Movie = apps.get_model('movies', 'Movie')
    
    # Get the movie details directly from database
    movie_obj = get_object_or_404(Movie, id=movie_id)
    
    # Convert to dictionary format
    movie = {
        "id": movie_obj.id,
        "title": movie_obj.title,
        "genre": movie_obj.genre,
        "poster_url": movie_obj.poster_url,
        "description": movie_obj.description
    }
    
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
            # Prepare movie information for the prompt
            movie_title = movie.get('title', 'this movie')
            movie_genre = movie.get('genre', '')
            movie_description = movie.get('description', '')
            movie_rating = movie.get('average_rating', 0)
            
            # Construct a prompt for the LLM
            prompt = f"""Based on the following information about '{movie_title}' (Genre: {movie_genre}, Rating: {movie_rating}/5):
            
            Description: {movie_description}
            
            Is this movie worth watching? Give me a review of this movie in an unhinged manner. If the movie is good, praise it like a die-hard fan, but if the movie is bad, trash it into the ground. Basically, review it like a toxic and strict reviewer."""
            
            # Make a request to Groq API with Llama 3
            groq_api_key = settings.GROQ_API_KEY
            
            # Debug the API key
            if not groq_api_key:
                print("GROQ_API_KEY is not set in environment variables")
                llm_recommendation = "Unable to generate a recommendation. API key not configured."
                # Don't return early, continue to render the template at the end of the function
            else:
                try:
                    # Ensure the API key is properly formatted (no quotes or whitespace)
                    groq_api_key = groq_api_key.strip().strip('"').strip("'")
                    print(f"Using GROQ API key: {groq_api_key[:5]}...")
                    
                    headers = {
                        "Authorization": f"Bearer {groq_api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "model": "llama3-70b-8192",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000  # Limit response length
                    }
                    
                    print("Sending request to Groq API...")
                    response = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30  # Add timeout to prevent hanging
                    )
                    
                    print(f"Groq API response status: {response.status_code}")
                    response_text = response.text
                    print(f"Response content: {response_text[:100]}...")  # Print first 100 chars of response
                    
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            if 'choices' in response_data and len(response_data['choices']) > 0:
                                if 'message' in response_data['choices'][0] and 'content' in response_data['choices'][0]['message']:
                                    llm_recommendation = response_data['choices'][0]['message']['content'].strip()
                                    print(f"Generated LLM recommendation for {movie_title}")
                                else:
                                    print("Response format unexpected: 'message' or 'content' not found in response")
                                    llm_recommendation = "Unable to parse the AI response. Please try again later."
                            else:
                                print("Response format unexpected: 'choices' not found or empty in response")
                                llm_recommendation = "Unable to parse the AI response. Please try again later."
                        except json.JSONDecodeError as json_err:
                            print(f"Error decoding JSON response: {str(json_err)}")
                            llm_recommendation = "Unable to parse the AI response. Please try again later."
                    else:
                        print(f"Error from Groq API: {response.status_code}, {response_text}")
                        llm_recommendation = "Unable to generate a recommendation at this time. Please try again later."
                except requests.exceptions.Timeout:
                    print("Timeout error when calling Groq API")
                    llm_recommendation = "The recommendation service is taking too long to respond. Please try again later."
                
        except requests.exceptions.RequestException as e:
            print(f"Request error when calling Groq API: {str(e)}")
            # Provide more specific error messages based on the type of exception
            if isinstance(e, requests.exceptions.ConnectionError):
                llm_recommendation = "Unable to connect to the recommendation service. Please check your internet connection and try again later."
            elif isinstance(e, requests.exceptions.Timeout):
                llm_recommendation = "The recommendation service is taking too long to respond. Please try again later."
            else:
                llm_recommendation = "Unable to connect to recommendation service. Please try again later."
        except Exception as e:
            print(f"Error generating LLM recommendation: {str(e)}")
            # Provide more context about the error
            error_type = type(e).__name__
            print(f"Exception type: {error_type}")
            
            # Give a more specific error message based on the error type
            if 'JSON' in error_type or 'json' in str(e).lower():
                llm_recommendation = "Unable to process the AI response format. Our team has been notified."
            elif 'key' in str(e).lower() or 'auth' in str(e).lower():
                llm_recommendation = "Authentication issue with our AI service. Please try again later."
            else:
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
    from django.apps import apps
    
    # Get the Movie model
    Movie = apps.get_model('movies', 'Movie')
    
    try:
        # Get a sample of movies as recommendations
        # In a real app, this would use a recommendation algorithm
        movie_queryset = Movie.objects.all().order_by('?')[:10]
        
        # Convert queryset to list of dictionaries
        recommended_movies = []
        for movie in movie_queryset:
            recommended_movies.append({
                "id": movie.id,
                "title": movie.title,
                "genre": movie.genre,
                "poster_url": movie.poster_url,
                "description": movie.description
            })
    except Exception as e:
        print(f"Error getting recommendations: {str(e)}")
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
    from django.apps import apps
    from movies.auth import ClerkJWTAuthentication
    
    # Get the Clerk token from the request headers or cookies
    clerk_token = request.COOKIES.get('clerk_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not clerk_token:
        return redirect('/login/')
    
    # Get user profile data using the Clerk token
    try:
        # Use the ClerkJWTAuthentication to get the user from the token
        auth = ClerkJWTAuthentication()
        user = auth.get_user_from_token(clerk_token)
        
        if user:
            # Get the UserProfile model
            UserProfile = apps.get_model('users', 'UserProfile')
            
            try:
                # Get the user profile
                user_profile = UserProfile.objects.get(clerk_user_id=user.get('id'))
                
                # Create user data dictionary
                user_data = {
                    "id": user_profile.user.id,
                    "username": user_profile.user.username,
                    "email": user_profile.user.email,
                    "first_name": user_profile.user.first_name,
                    "last_name": user_profile.user.last_name,
                    "clerk_user_id": user_profile.clerk_user_id
                }
                
                # Get user's ratings directly from database
                Rating = apps.get_model('movies', 'Rating')
                ratings = Rating.objects.filter(user_id=user.get('id'))
                
                # Convert ratings to list of dictionaries
                ratings_data = []
                for rating in ratings:
                    ratings_data.append({
                        "id": rating.id,
                        "movie": {
                            "id": rating.movie.id,
                            "title": rating.movie.title,
                            "genre": rating.movie.genre,
                            "poster_url": rating.movie.poster_url
                        },
                        "rating": rating.rating,
                        "review": rating.review
                    })
            except UserProfile.DoesNotExist:
                return redirect('/login/')
        else:
            return redirect('/login/')
        
        # Render the profile template with user data and ratings
        return render(request, 'users/profile.html', {
            'user': user_data,
            'ratings': ratings_data
        })
    except Exception as e:
        # Handle any errors
        print(f"Profile view error: {str(e)}")
        return render(request, 'error.html', {
            'error': str(e)
        })

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
    from django.db.models import Q
    from django.apps import apps
    
    search_query = request.GET.get('q', '')
    
    if not search_query:
        return redirect('movie_list')

    print(f"Search query: {search_query}")
    
    # Get the Movie model
    Movie = apps.get_model('movies', 'Movie')
    
    try:
        # Search for movies by title or genre directly from database
        movies_queryset = Movie.objects.filter(
            Q(title__icontains=search_query) | 
            Q(genre__icontains=search_query)
        )
        
        # Convert queryset to list of dictionaries
        movies = []
        for movie in movies_queryset:
            movies.append({
                "id": movie.id,
                "title": movie.title,
                "genre": movie.genre,
                "poster_url": movie.poster_url,
                "description": movie.description
            })
    except Exception as e:
        print(f"Error searching movies: {str(e)}")
        movies = []

    # Get genres for filter dropdown directly from database
    try:
        genres = list(Movie.objects.values_list('genre', flat=True).distinct())
        genres = sorted(genres)
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