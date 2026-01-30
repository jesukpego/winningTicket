# Migration to remove organizer_type and organizer_user fields from Game model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0003_remove_userprofile_daily_limit_and_more'),
    ]

    operations = [
        # Remove organizer_user field
        migrations.RemoveField(
            model_name='game',
            name='organizer_user',
        ),
        # Remove organizer_type field
        migrations.RemoveField(
            model_name='game',
            name='organizer_type',
        ),
        # Make company field required (non-nullable)
        migrations.AlterField(
            model_name='game',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='games',
                to='principal.company',
                verbose_name='Company Organizer'
            ),
        ),
    ]
