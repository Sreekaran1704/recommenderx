from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
from .models import Movie, Rating, Watchlist

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
