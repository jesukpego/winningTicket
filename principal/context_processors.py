from .models import Company, Winner
from django.db.models import Sum

def navigation_context(request):
    top_winner = Winner.objects.select_related('user', 'draw__game').order_by('-prize_amount').first()
    return {
        'companies': Company.objects.filter(is_active=True),
        'nav_top_winner': top_winner,
    }
