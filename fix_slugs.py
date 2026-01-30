
import os
import django
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from principal.models import Game
import time

print("Checking games...")
games = Game.objects.all()
for game in games:
    print(f"Checking Game ID {game.id}: Name='{game.name}', Slug='{game.slug}'")
    
    needs_save = False
    
    if not game.slug or game.slug.strip() == "":
        print(f" -> Empty slug found for game {game.id}")
        new_slug = slugify(game.name)
        if not new_slug:
            # Fallback if name is non-ascii or empty
            new_slug = f"game-{game.id}-{int(time.time())}"
        
        game.slug = new_slug
        needs_save = True
        print(f" -> Generated new slug: {game.slug}")
    
    if needs_save:
        game.save()
        print(" -> Saved!")
        
print("Done.")
