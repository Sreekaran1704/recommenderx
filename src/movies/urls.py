from django.urls import path
from .views import movie_list, movie_detail, add_rating, create_watchlist

urlpatterns = [
    path('movies/', movie_list, name='movie_list'),
    path('movies/<int:movie_id>/', movie_detail, name='movie_detail'),
    path('ratings/add/', add_rating, name='add_rating'),
    path('watchlist/add/', create_watchlist, name='create_watchlist'),
]
