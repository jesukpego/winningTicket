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


def faq(request):
    return render(request, 'winning_ticket/faq.html')

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

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            if not remember_me:
                # Session expires when browser closes
                request.session.set_expiry(0)
            else:
                # Session lasts 2 weeks (default) or configured time
                request.session.set_expiry(1209600)  # 2 weeks
                
            messages.success(request, f"Welcome back, {user.username}!")
            
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'users/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')
        
        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'users/register.html', {
                'values': request.POST
            })
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return render(request, 'users/register.html', {
                'values': request.POST
            })
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return render(request, 'users/register.html', {
                'values': request.POST
            })
            
        # Create User
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.save()
            messages.success(request, "Account created successfully! You can now login.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return render(request, 'users/register.html', {
                'values': request.POST
            })
            
    return render(request, 'users/register.html')


def dashboard(request):
    return render(request, 'users/dashboard.html')
