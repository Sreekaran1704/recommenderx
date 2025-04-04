from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rating',
            name='user_email',
            field=models.EmailField(max_length=254, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rating',
            name='user_name',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
    ]
