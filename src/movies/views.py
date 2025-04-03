from django.db.models import Q
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .auth import ClerkJWTAuthentication
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework import status
from django.apps import apps

# Remove direct model imports and use apps.get_model consistently

@api_view(['GET'])
@authentication_classes([ClerkJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_movie_recommendations(request):
    try:
        # Import recommendation function
        from .recommendation import get_recommendations
        
        # Get the user ID directly from Clerk authentication
        clerk_user_id = request.user.get('id')
        
        # Get recommendations using the Clerk user ID
        recommended_movies = get_recommendations(clerk_user_id)
        
        # Serialize the movies
        movies_data = []
        for movie in recommended_movies:
            movies_data.append({
                "id": movie.id,
                "title": movie.title,
                "genre": movie.genre,
                "poster_url": movie.poster_url,
                "description": movie.description
            })
        
        return Response({"recommendations": movies_data})
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([ClerkJWTAuthentication])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": "This is a protected view. You are authenticated!"})

def movie_list(request):
    Movie = apps.get_model('movies', 'Movie')
    movies = list(Movie.objects.all().values())
    return JsonResponse(movies, safe=False)

def movie_detail(request, movie_id):
    Movie = apps.get_model('movies', 'Movie')
    movie = get_object_or_404(Movie, id=movie_id)
    return JsonResponse({
        "title": movie.title, 
        "genre": movie.genre, 
        "poster_url": movie.poster_url, 
        "description": movie.description
    })

@csrf_exempt
def add_rating(request):
    if request.method == 'POST':
        Movie = apps.get_model('movies', 'Movie')
        Rating = apps.get_model('movies', 'Rating')
        
        data = json.loads(request.body)
        user_id = data.get('user_id')
        movie_id = data.get('movie_id')
        rating_value = data.get('rating')
        review = data.get('review', '')
        user_name = data.get('user_name', '')
        user_email = data.get('user_email', '')
        
        if not user_id or not movie_id or not rating_value:
            return JsonResponse({"error": "User ID, movie ID, and rating are required"}, status=400)
            
        movie = get_object_or_404(Movie, id=movie_id)
        
        rating, created = Rating.objects.update_or_create(
            user_id=user_id,
            movie=movie,
            defaults={
                'rating': rating_value,
                'review': review,
                'user_name': user_name,
                'user_email': user_email
            }
        )
        
        return JsonResponse({"message": "Rating added successfully", "rating_id": rating.id})
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def create_watchlist(request):
    if request.method == 'POST':
        Movie = apps.get_model('movies', 'Movie')
        Watchlist = apps.get_model('movies', 'Watchlist')
        
        data = json.loads(request.body)
        user_id = data.get('user_id')
        movie_id = data.get('movie_id')
        
        if not user_id or not movie_id:
            return JsonResponse({"error": "Both user_id and movie_id are required"}, status=400)
            
        movie = get_object_or_404(Movie, id=movie_id)
        
        # Create or get watchlist entry
        watchlist, created = Watchlist.objects.get_or_create(
            user_id=user_id,
            movie=movie
        )
        
        return JsonResponse({"message": "Movie added to watchlist"})
    return JsonResponse({"error": "Invalid request"}, status=400)

@api_view(['POST'])
@authentication_classes([ClerkJWTAuthentication])
@permission_classes([IsAuthenticated])
def remove_from_watchlist(request):
    try:
        Movie = apps.get_model('movies', 'Movie')
        Watchlist = apps.get_model('movies', 'Watchlist')
        
        movie_id = request.data.get('movie_id')
        if not movie_id:
            return Response({"error": "Movie ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get the user ID from Clerk authentication
        clerk_user_id = request.user.get('id')
        
        # Find the watchlist entry
        try:
            movie = Movie.objects.get(id=movie_id)
            watchlist_entry = Watchlist.objects.get(user_id=clerk_user_id, movie=movie)
            watchlist_entry.delete()
            return Response({"message": "Movie removed from watchlist successfully"})
        except Watchlist.DoesNotExist:
            return Response({"error": "Movie not in watchlist"}, status=status.HTTP_404_NOT_FOUND)
        
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([ClerkJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_watchlist(request):
    try:
        Watchlist = apps.get_model('movies', 'Watchlist')
        
        # Get the user ID from Clerk authentication
        clerk_user_id = request.user.get('id')
        
        # Get watchlist items for this user
        watchlist_items = Watchlist.objects.filter(user_id=clerk_user_id)
        
        # Serialize the watchlist movies
        movies_data = []
        for item in watchlist_items:
            movie = item.movie
            movies_data.append({
                "id": movie.id,
                "title": movie.title,
                "genre": movie.genre,
                "poster_url": movie.poster_url,
                "description": movie.description
            })
        
        return Response({"watchlist": movies_data})
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def search_movies(request):
    try:
        Movie = apps.get_model('movies', 'Movie')
        
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Search query is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Search for movies by title or genre
        movies = Movie.objects.filter(
            Q(title__icontains=query) | 
            Q(genre__icontains=query)
        )
        
        # Serialize the movies
        movies_data = []
        for movie in movies:
            movies_data.append({
                "id": movie.id,
                "title": movie.title,
                "genre": movie.genre,
                "poster_url": movie.poster_url,
                "description": movie.description
            })
        
        return Response({"results": movies_data})
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@authentication_classes([ClerkJWTAuthentication])
@permission_classes([IsAuthenticated])
def update_rating(request):
    try:
        Movie = apps.get_model('movies', 'Movie')
        Rating = apps.get_model('movies', 'Rating')
        
        movie_id = request.data.get('movie_id')
        new_rating = request.data.get('rating')
        new_review = request.data.get('review', '')
        
        if not movie_id or not new_rating:
            return Response({"error": "Movie ID and rating are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the user ID from Clerk authentication
        clerk_user_id = request.user.get('id')
        
        # Find the existing rating
        try:
            movie = Movie.objects.get(id=movie_id)
            rating, created = Rating.objects.update_or_create(
                user_id=clerk_user_id,
                movie=movie,
                defaults={
                    'rating': new_rating,
                    'review': new_review,
                    'user_name': request.user.get('first_name', '') + ' ' + request.user.get('last_name', ''),
                    'user_email': request.user.get('email_addresses', [{}])[0].get('email_address', '')
                }
            )
            
            return Response({"message": "Rating updated successfully"})
        except Movie.DoesNotExist:
            return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([ClerkJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_ratings(request):
    try:
        Rating = apps.get_model('movies', 'Rating')
        
        # Get the user ID from Clerk authentication
        clerk_user_id = request.user.get('id')
        
        # Get all ratings by this user
        ratings = Rating.objects.filter(user_id=clerk_user_id)
        
        # Serialize the ratings
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
                "review": rating.review,
                "created_at": rating.created_at.isoformat() if hasattr(rating, 'created_at') else None
            })
        
        return Response({"ratings": ratings_data})
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_movie_ratings(request, movie_id):
    try:
        Movie = apps.get_model('movies', 'Movie')
        Rating = apps.get_model('movies', 'Rating')
        
        # Get the movie
        movie = get_object_or_404(Movie, id=movie_id)
        
        # Get all ratings for this movie
        ratings = Rating.objects.filter(movie=movie)
        
        # Calculate average rating
        total_rating = 0
        count = 0
        for rating in ratings:
            total_rating += rating.rating
            count += 1
        
        avg_rating = total_rating / count if count > 0 else 0
        
        # Serialize the ratings
        ratings_data = []
        for rating in ratings:
            ratings_data.append({
                "id": rating.id,
                "user": rating.user_name or rating.user_id,  # Use user_name if available, otherwise user_id
                "rating": rating.rating,
                "review": rating.review,
                "created_at": rating.created_at.isoformat() if hasattr(rating, 'created_at') else None
            })
        
        return Response({
            "movie": {
                "id": movie.id,
                "title": movie.title,
                "genre": movie.genre,
                "poster_url": movie.poster_url,
                "description": movie.description
            },
            "average_rating": avg_rating,
            "ratings_count": count,
            "ratings": ratings_data
        })
    
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_movies_by_genre(request, genre):
    try:
        Movie = apps.get_model('movies', 'Movie')
        
        # Get all movies with the specified genre
        movies = Movie.objects.filter(genre__icontains=genre)
        
        if not movies.exists():
            return Response({"message": "No movies found for this genre"}, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize the movies
        movies_data = []
        for movie in movies:
            movies_data.append({
                "id": movie.id,
                "title": movie.title,
                "genre": movie.genre,
                "poster_url": movie.poster_url,
                "description": movie.description
            })
        
        return Response({
            "genre": genre,
            "count": len(movies_data),
            "movies": movies_data
        })
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_all_genres(request):
    try:
        Movie = apps.get_model('movies', 'Movie')
        
        # Get all unique genres from the movies
        all_genres = Movie.objects.values_list('genre', flat=True).distinct()
        
        # Convert to a list and sort alphabetically
        genres_list = sorted(list(all_genres))
        
        return Response({"genres": genres_list})
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)