import numpy as np
from django.contrib.auth.models import User
from .models import Movie, Rating
from sklearn.metrics.pairwise import cosine_similarity

def get_recommendations(user_id, num_recommendations=5):
    """
    Generate movie recommendations for a user using collaborative filtering.
    
    Args:
        user_id: The ID of the user to generate recommendations for
        num_recommendations: Number of recommendations to return
        
    Returns:
        List of recommended movie objects
    """
    # Get all ratings
    ratings = Rating.objects.all()
    
    # Get all users and movies
    users = User.objects.all()
    movies = Movie.objects.all()
    
    # Create user-movie matrix
    user_movie_matrix = np.zeros((users.count(), movies.count()))
    
    # Fill the matrix with ratings
    user_indices = {user.id: i for i, user in enumerate(users)}
    movie_indices = {movie.id: i for i, movie in enumerate(movies)}
    
    for rating in ratings:
        user_idx = user_indices.get(rating.user.id)
        movie_idx = movie_indices.get(rating.movie.id)
        if user_idx is not None and movie_idx is not None:
            user_movie_matrix[user_idx, movie_idx] = rating.rating
    
    # Calculate user similarity
    user_similarity = cosine_similarity(user_movie_matrix)
    
    # Get the user index
    user_idx = user_indices.get(user_id)
    if user_idx is None:
        return []
    
    # Get similar users
    similar_users = user_similarity[user_idx]
    
    # Get the user's rated movies
    user_ratings = Rating.objects.filter(user_id=user_id)
    rated_movie_ids = [rating.movie.id for rating in user_ratings]
    
    # Calculate predicted ratings for unrated movies
    recommendations = []
    
    for movie in movies:
        if movie.id not in rated_movie_ids:
            movie_idx = movie_indices.get(movie.id)
            if movie_idx is not None:
                # Calculate weighted rating
                weighted_sum = 0
                similarity_sum = 0
                
                for other_user_idx, similarity in enumerate(similar_users):
                    if similarity > 0 and other_user_idx != user_idx:
                        rating = user_movie_matrix[other_user_idx, movie_idx]
                        if rating > 0:
                            weighted_sum += similarity * rating
                            similarity_sum += similarity
                
                if similarity_sum > 0:
                    predicted_rating = weighted_sum / similarity_sum
                    recommendations.append((movie, predicted_rating))
    
    # Sort by predicted rating and return top N
    recommendations.sort(key=lambda x: x[1], reverse=True)
    return [movie for movie, _ in recommendations[:num_recommendations]]