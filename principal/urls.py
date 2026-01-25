from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),  # ← ROOT (CRITIQUE)
    path("accueil/", views.accueil, name="accueil"),
    path("faq/", views.faq, name="faq"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("games/", views.games, name="games"),
    path("game/<int:game_id>/", views.game_detail, name="game_detail"),
    path("buy-ticket/", views.buy_ticket, name="buy_ticket"),
    path("my-tickets/", views.my_tickets, name="my_tickets"),
    path("winners/", views.winners, name="winners"),
    path("results/", views.results, name="results"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("health/", views.health_check, name="health"),
    
    # Admin
    path("manage-games/", views.manage_games, name="manage_games"),
    path("manage-games/create/", views.create_game, name="create_game"),
    path("manage-games/edit/<int:game_id>/", views.edit_game, name="edit_game"),
    path("manage-games/delete/<int:game_id>/", views.delete_game, name="delete_game"),
]
