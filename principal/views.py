from django.shortcuts import render

def accueil(request):
    return render(request, 'winning_ticket/indx.html')


from django.shortcuts import render

def home(request):
    return render(request, 'winning_ticket/index.html')

def games(request):
    return render(request, 'winning_ticket/games.html')

def about(request):
    return render(request, 'winning_ticket/about.html')

def contact(request):
    return render(request, 'winning_ticket/contact.html')


# In principal/views.py, make sure you have this function:

def game_detail(request, game_id):
    """Game detail page"""
    # You can pass game data here if you want
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

def login_view(request):
    return render(request, 'users/login.html')

def dashboard(request):
    return render(request, 'users/dashboard.html')
def register_view(request):
    return render(request, 'users/register.html')

def winners(request):
    """Winners gallery page"""
    return render(request, 'winning_ticket/winners.html')