from django.apps import AppConfig


class MoviesConfig(AppConfig):
    name = 'movies'
    
    @property
    def default_auto_field(self):
        return 'django.db.models.BigAutoField'
    
    def ready(self):
        # This will ensure models are properly loaded when the app is ready
        pass