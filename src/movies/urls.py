from django.urls import path
from . import views

urlpatterns = [
    path('movies/', views.movie_list, name='movie_list'),
    path('movies/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('movies/search/', views.search_movies, name='search_movies'),
    path('movies/genres/', views.get_all_genres, name='get_all_genres'),
    path('movies/genre/<str:genre>/', views.get_movies_by_genre, name='get_movies_by_genre'),

    path('ratings/add/', views.add_rating, name='add_rating'),
    path('ratings/update/', views.update_rating, name='update_rating'),
    path('ratings/user/', views.get_user_ratings, name='user_rating'),
    path('ratings/movie/<int:movie_id>/', views.get_movie_ratings, name='get_movie_ratings'),
    
    
    path('watchlist/add/', views.create_watchlist, name='create_watchlist'),
    path('watchlist/remove/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('watchlist/', views.get_user_watchlist, name='get_user_watchlist'),


    path('protected/', views.protected_view, name='protected_view'),
    path('recommendations/', views.get_movie_recommendations, name='movie_recommendations')
]
