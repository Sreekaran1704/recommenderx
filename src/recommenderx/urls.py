"""
URL configuration for recommenderx project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include,path
from .views import home_page_view, movie_list_view, movie_detail_view, recommendations_view, watchlist_view, add_to_watchlist_view, login_view, signup_view, logout_view, profile_view
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path("", home_page_view),
    path("movies/", movie_list_view),
    path("movies/<int:movie_id>/", movie_detail_view),
    path("recommendations/", recommendations_view),
    path("watchlist/", watchlist_view),
    path("watchlist/add/", add_to_watchlist_view),
    path("login/", login_view),
    path("signup/", signup_view),
    path("logout/", logout_view),
    path("profile/", profile_view),
    path("api/", include("movies.urls")),
    path("api/users/", include("users.urls")),
    path("admin/", admin.site.urls),
    #path("api-docs/", include_docs_urls(title="Movie Recommendation API"))
]
