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