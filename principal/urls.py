from django.urls import path
from .views import accueil
from . import views

urlpatterns = [
    path('accueil/', accueil, name='accueil'),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('games/', views.games, name='games'),
    # In principal/urls.py, make sure you have:
path('game/<int:game_id>/', views.game_detail, name='game_detail'),
    path('buy-ticket/', views.buy_ticket, name='buy_ticket'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    # Add this line to principal/urls.py
path('winners/', views.winners, name='winners'),
    path('results/', views.results, name='results'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
