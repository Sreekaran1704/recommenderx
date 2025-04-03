import requests
from django.core.management.base import BaseCommand
from movies.models import Movie

API_KEY = "3fd0e77c338bfaa9f9986edc98c2511b"
TMDB_SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'

class Command(BaseCommand):
    help = 'Fetch and save movie poster URLs using TMDB API'

    def handle(self, *args, **kwargs):
        movies = Movie.objects.all()

        for movie in movies:
            response = requests.get(TMDB_SEARCH_URL, params={
                'api_key': API_KEY,
                'query': movie.title
            })

            if response.status_code == 200:
                results = response.json().get('results')
                if results:
                    poster_path = results[0].get('poster_path')
                    if poster_path:
                        movie.poster_url = f'{TMDB_IMAGE_BASE}{poster_path}'
                        movie.save()
                        self.stdout.write(self.style.SUCCESS(f'✅ {movie.title} poster saved.'))
                    else:
                        self.stdout.write(self.style.WARNING(f'⚠️ {movie.title} has no poster.'))
                else:
                    self.stdout.write(self.style.ERROR(f'❌ No results for {movie.title}.'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ API failed for {movie.title}.'))
