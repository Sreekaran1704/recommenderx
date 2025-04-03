from django.contrib import admin
from django.urls import include, path
from .views import home_page_view, movie_list_view, movie_detail_view, recommendations_view, watchlist_view, add_to_watchlist_view, login_view, signup_view, logout_view, profile_view
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    # Main pages with named URLs for better navigation
    path("", home_page_view, name="home"),
    path("movies/", movie_list_view, name="movie_list"),
    path("movies/<int:movie_id>/", movie_detail_view, name="movie_detail"),
    path("recommendations/", recommendations_view, name="recommendations"),
    
    # User-specific pages
    path("watchlist/", watchlist_view, name="watchlist"),
    path("watchlist/add/", add_to_watchlist_view, name="add_to_watchlist"),
    
    # Authentication routes
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    
    # API routes
    path("api/", include("movies.urls")),
    path("api/users/", include("users.urls")),
    
    # Admin and documentation
    path("admin/", admin.site.urls),
    #path("api-docs/", include_docs_urls(title="Movie Recommendation API"))
]
