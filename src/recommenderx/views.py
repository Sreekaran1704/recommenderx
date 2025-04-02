from django.http import HttpResponse
from django.shortcuts import render, redirect
import requests

def home_page_view(request, *args, **kwargs):

    return render(request, 'home.html')

def movie_list_view(request):

    search_query = request.GET.get('q', '')
    genre_filter = request.GET.get('genre', '')

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
    
    # Get genres for filter dropdown
    genres_response = requests.get('http://localhost:8000/api/movies/genres/')
    genres = genres_response.json().get('genres', [])
    
    return render(request, 'movies/movie_list.html', {
        'movies': movies,
        'genres': genres
    })

def movie_detail_view(request, movie_id):

    response = requests.get(f'http://localhost:8000/api/movies/{movie_id}/')
    movie = response.json()

    try:
        ratings_response = requests.get(f'http://localhost:8000/api/ratings/movie/{movie_id}/')
        ratings_data = ratings_response.json()
        ratings = ratings_data.get('ratings', [])
        average_rating = ratings_data.get('average_rating', 0)
        ratings_count = ratings_data.get('ratings_count', 0)
    
    except :
        ratings = []
        average_rating = 0
        ratings_count = 0
    
    return render(request, 'movies/movie_detail.html', {
        'movie': movie,
        'ratings': ratings,
        'average_rating': average_rating,
        'ratings_count': ratings_count
    })

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