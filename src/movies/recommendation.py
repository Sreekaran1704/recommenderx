from django.apps import apps

def get_recommendations(user_id, num_recommendations=5):
    """
    Generate movie recommendations for a user.
    """
    # Get model classes using apps.get_model
    Movie = apps.get_model('movies', 'Movie')
    Rating = apps.get_model('movies', 'Rating')
    
    try:
        # Get popular movies as fallback
        popular_movies = list(Movie.objects.all()[:num_recommendations])
        
        # Check if we have any ratings at all
        if Rating.objects.count() == 0:
            return popular_movies
        
        # Check if this user has any ratings
        user_ratings = Rating.objects.filter(user_id=user_id)
        if not user_ratings.exists():
            return popular_movies
            
        # Get movies this user has already rated
        rated_movie_ids = [rating.movie_id for rating in user_ratings]
        
        # Find users with similar tastes
        # Get all users who rated at least one movie that this user rated
        similar_user_ratings = Rating.objects.filter(movie_id__in=rated_movie_ids).exclude(user_id=user_id)
        similar_user_ids = similar_user_ratings.values_list('user_id', flat=True).distinct()
        
        # Get movies rated highly by similar users that this user hasn't rated yet
        recommended_movies = Rating.objects.filter(
            user_id__in=similar_user_ids,
            rating__gte=4  # Only consider high ratings (4 or 5)
        ).exclude(
            movie_id__in=rated_movie_ids
        ).values_list('movie_id', flat=True).distinct()
        
        # Get the actual movie objects
        recommendations = list(Movie.objects.filter(id__in=recommended_movies)[:num_recommendations])
        
        # If we don't have enough recommendations, add some popular movies
        if len(recommendations) < num_recommendations:
            # Get IDs of movies we already recommended
            recommended_ids = [movie.id for movie in recommendations]
            
            # Add popular movies not already in recommendations
            additional_movies = list(Movie.objects.exclude(
                id__in=recommended_ids + rated_movie_ids
            )[:num_recommendations - len(recommendations)])
            
            # Combine the recommendations
            recommendations = recommendations + additional_movies
        
        return recommendations
        
    except Exception as e:
        # If anything goes wrong, return some popular movies
        print(f"Error in recommendation system: {str(e)}")
        return list(Movie.objects.all()[:num_recommendations])