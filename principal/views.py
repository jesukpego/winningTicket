from urllib import request
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_GET


# ======================================================
# HEALTHCHECK (RAILWAY / RENDER)
# ======================================================

@require_GET
def health_check(request):
    """
    Endpoint de santé pour Railway.
    Retourne toujours 200 OK, sans template, sans DB.
    """
    return HttpResponse("OK", status=200)


def home(request):
    """
    ⚠️ MODIFIÉ
    AVANT : rendait un template HTML (index.html)
    PROBLÈME : Railway échoue si le template/static/DB casse

    MAINTENANT :
    Retourne un simple OK pour garantir le healthcheck
    """
    #return HttpResponse("OK")
    return render(request, 'winning_ticket/index.html')


# ======================================================
# PAGES HTML (inchangées)
# ======================================================

def accueil(request):
    return render(request, 'winning_ticket/indx.html')


def games(request):
    return render(request, 'winning_ticket/games.html')


def about(request):
    return render(request, 'winning_ticket/about.html')


def contact(request):
    return render(request, 'winning_ticket/contact.html')


def game_detail(request, game_id):
    """
    Page détail d’un jeu
    """
    context = {
        'game_id': game_id,
    }
    return render(request, 'winning_ticket/game_detail.html', context)


def buy_ticket(request):
    return render(request, 'winning_ticket/buy_ticket.html')


def my_tickets(request):
    return render(request, 'winning_ticket/my_tickets.html')


def results(request):
    return render(request, 'winning_ticket/results.html')


def winners(request):
    """
    Galerie des gagnants
    """
    return render(request, 'winning_ticket/winners.html')


# ======================================================
# AUTH / DASHBOARD
# ======================================================

def login_view(request):
    return render(request, 'users/login.html')


def register_view(request):
    return render(request, 'users/register.html')


def dashboard(request):
    return render(request, 'users/dashboard.html')
