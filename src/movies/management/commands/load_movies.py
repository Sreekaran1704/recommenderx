import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from movies.models import Movie

class Command(BaseCommand):
    help = 'Load movies from CSV file into the Movie model'

    def handle(self, *args, **kwargs):
        with open('Movies_dataset.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                title = row['Movie_title']
                genre = row['genres']
                description = row['Logline']
                date_str = row['Lunch_date']

                # Convert date string to proper format
                try:
                    release_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                except ValueError:
                    self.stdout.write(self.style.WARNING(f"⚠️ Skipping {title}: invalid date format"))
                    continue

                # Save to DB
                movie, created = Movie.objects.get_or_create(
                    title=title,
                    defaults={
                        'genre': genre,
                        'description': description,
                        'release_date': release_date,
                        'poster_url': '',  # Will be added later
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"✅ Added: {title}"))
                else:
                    self.stdout.write(self.style.WARNING(f"ℹ️ Already exists: {title}"))
