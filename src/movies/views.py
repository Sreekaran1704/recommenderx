from django.db.models import Q
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .auth import ClerkJWTAuthentication
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
from .models import Movie, Rating, Watchlist
from .recommendation import get_recommendations
from users.models import UserProfile
from rest_framework import status

@api_view(['GET'])
@authentication_classes([ClerkJWTAuthentication])
@permission_classes([IsAuthenticated])

def get_movie_recommendations(request):
    try:
        # Get the user profile from Clerk user ID
        clerk_user_id = request.user.get('id')
        user_profile = UserProfile.objects.get(clerk_user_id=clerk_user_id)
        
        # Get recommendations
        recommended_movies = get_recommendations(user_profile.user.id)
        
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
    
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])  # Add these decorators to protected_view
@authentication_classes([ClerkJWTAuthentication])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": "This is a protected view. You are authenticated!"})
def movie_list(request):
    movies = Movie.objects.all().values()
    return JsonResponse(list(movies), safe=False)

def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    return JsonResponse({"title": movie.title, "genre": movie.genre, "poster_url": movie.poster_url, "description": movie.description})

@csrf_exempt
def add_rating(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = get_object_or_404(User, id=data['user_id'])
        movie = get_object_or_404(Movie, id=data['movie_id'])
        rating = Rating.objects.create(user=user, movie=movie, rating=data['rating'], review=data.get('review', ''))
        return JsonResponse({"message": "Rating added successfully", "rating_id": rating.id})
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def create_watchlist(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = get_object_or_404(User, id=data['user_id'])
        watchlist, created = Watchlist.objects.get_or_create(user=user)
        movie = get_object_or_404(Movie, id=data['movie_id'])
        watchlist.movies.add(movie)
        return JsonResponse({"message": "Movie added to watchlist"})
    return JsonResponse({"error": "Invalid request"}, status=400)

@api_view(['POST'])
@authentication_classes([ClerkJWTAuthentication])
@permission_classes([IsAuthenticated])
def remove_from_watchlist(request):
    try:
        movie_id = request.data.get('movie_id')
        if not movie_id:
            return Response({"error": "Movie ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get the user profile from Clerk user ID
        clerk_user_id = request.user.get('id')
        user_profile = UserProfile.objects.get(clerk_user_id=clerk_user_id)
        
        # Get watchlist
        try:
            watchlist = Watchlist.objects.get(user=user_profile.user)
            movie = Movie.objects.get(id=movie_id)
            watchlist.movies.remove(movie)
            return Response({"message": "Movie removed from watchlist successfully"})
        except Watchlist.DoesNotExist:
            return Response({"error": "Watchlist not found"}, status=status.HTTP_404_NOT_FOUND)
        
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([ClerkJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_watchlist(request):
    try:
        # Get the user profile from Clerk user ID
        clerk_user_id = request.user.get('id')
        user_profile = UserProfile.objects.get(clerk_user_id=clerk_user_id)
        
        # Get or create watchlist
        watchlist, created = Watchlist.objects.get_or_create(user=user_profile.user)
        
        # Serialize the watchlist movies
        movies_data = []
        for movie in watchlist.movies.all():
            movies_data.append({
                "id": movie.id,
                "title": movie.title,
                "genre": movie.genre,
                "poster_url": movie.poster_url,
                "description": movie.description
            })
        
        return Response({"watchlist": movies_data})
    
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def search_movies(request):
    try:
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
        movie_id = request.data.get('movie_id')
        new_rating = request.data.get('rating')
        new_review = request.data.get('review', '')
        
        if not movie_id or not new_rating:
            return Response({"error": "Movie ID and rating are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the user profile from Clerk user ID
        clerk_user_id = request.user.get('id')
        user_profile = UserProfile.objects.get(clerk_user_id=clerk_user_id)
        
        # Find the existing rating
        try:
            rating = Rating.objects.get(user=user_profile.user, movie_id=movie_id)
            
            # Update the rating
            rating.rating = new_rating
            rating.review = new_review
            rating.save()
            
            return Response({"message": "Rating updated successfully"})
        except Rating.DoesNotExist:
            return Response({"error": "Rating not found"}, status=status.HTTP_404_NOT_FOUND)
        
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([ClerkJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_ratings(request):
    try:
        # Get the user profile from Clerk user ID
        clerk_user_id = request.user.get('id')
        user_profile = UserProfile.objects.get(clerk_user_id=clerk_user_id)
        
        # Get all ratings by this user
        ratings = Rating.objects.filter(user=user_profile.user)
        
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
    
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_movie_ratings(request, movie_id):
    try:
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
                "user": rating.user.username,
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
        # Get all unique genres from the movies
        all_genres = Movie.objects.values_list('genre', flat=True).distinct()
        
        # Convert to a list and sort alphabetically
        genres_list = sorted(list(all_genres))
        
        return Response({"genres": genres_list})
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)