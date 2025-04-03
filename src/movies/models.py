from django.db import models

# Create your models here.
class Movie(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=255)
    release_date = models.DateField()
    poster_url = models.URLField()
    description = models.TextField()
    
    def __str__(self):
        if not hasattr(self, 'title') or self.title is None:
            return f"Movie {getattr(self, 'id', 'New')}"
        return str(self.title)

class Rating(models.Model):
    # Store Clerk user ID
    user_id = models.CharField(max_length=255, null=True, blank=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField()
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Store user information for display
    user_email = models.EmailField(blank=True, null=True)
    user_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        # Ensure a user can only rate a movie once
        unique_together = ('user_id', 'movie')

    def __str__(self):
        display_name = getattr(self, 'user_name', None) or getattr(self, 'user_id', 'Unknown User')
        rating_value = getattr(self, 'rating', 'Unknown')
        
        try:
            if hasattr(self, 'movie') and self.movie is not None:
                movie_title = getattr(self.movie, 'title', 'Unknown Movie')
            else:
                movie_title = 'Unknown Movie'
        except:
            movie_title = 'Unknown Movie'
            
        return f"{display_name} - {movie_title} - {rating_value}"

class Watchlist(models.Model):
    # Store Clerk user ID
    user_id = models.CharField(max_length=255, null=True, blank=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watchlists')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure a movie is only in a user's watchlist once
        unique_together = ('user_id', 'movie')

    def __str__(self):
        user = getattr(self, 'user_id', 'Unknown User')
        
        try:
            if hasattr(self, 'movie') and self.movie is not None:
                movie_title = getattr(self.movie, 'title', 'Unknown Movie')
            else:
                movie_title = 'Unknown Movie'
        except:
            movie_title = 'Unknown Movie'
            
        return f"{user} - {movie_title}"