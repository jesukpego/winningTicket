from urllib import request
import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.db import transaction, models
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django import forms
from django.utils import timezone
from .models import Game, Company, Wallet, Ticket, Payment

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
    """
    Page listant les jeux disponibles.
    Permet de filtrer par entreprise.
    """
    # Récupérer tous les jeux actifs
    games = Game.objects.filter(status='active').select_related('company').order_by('ticket_price')
    
    # Récupérer les entreprises actives qui ont des jeux actifs
    companies = Company.objects.filter(is_active=True, games__status='active').distinct()
    
    # Filtrage par entreprise
    company_filter = request.GET.get('company')
    if company_filter:
        try:
            company_id = int(company_filter)
            games = games.filter(company_id=company_id)
        except ValueError:
            pass
            
    context = {
        'games': games,
        'companies': companies,
        'selected_company': int(company_filter) if company_filter and company_filter.isdigit() else None
    }
    return render(request, 'winning_ticket/games.html', context)

def generate_ticket_id():
    """Génère un ID unique pour le billet"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

@login_required
def play_game(request, slug):
    """
    Page pour jouer à un jeu spécifique (acheter un billet).
    """
    game = get_object_or_404(Game, slug=slug, status='active')
    
    # Récupérer ou créer le wallet principal de l'utilisateur
    user_wallet, created = Wallet.objects.get_or_create(
        user=request.user, 
        wallet_type='main',
        defaults={'balance': 0}
    )
    
    # Récupérer les numéros déjà joués pour ce jeu
    taken_numbers = set()
    existing_tickets = Ticket.objects.filter(game=game)
    for t in existing_tickets:
        if isinstance(t.numbers, list):
            taken_numbers.update(t.numbers)

    if request.method == 'POST':
        # Récupérer les numéros sélectionnés
        selected_numbers_raw = request.POST.getlist('numbers')
        selected_numbers = [int(n) for n in selected_numbers_raw if n.isdigit()]
        
        # Validation du nombre de numéros
        if not selected_numbers:
            messages.error(request, "Veuillez sélectionner au moins un numéro.")
            return redirect('play_game', slug=slug)

        # Validation: Vérifier si les numéros sont déjà pris
        for num in selected_numbers:
            if num in taken_numbers:
                messages.error(request, f"Le numéro {num} a déjà été acheté par un autre joueur.")
                return redirect('play_game', slug=slug)

        # Validation du solde
        if user_wallet.balance < game.ticket_price:
            messages.error(request, "Solde insuffisant. Veuillez recharger votre portefeuille.")
            return redirect('play_game', slug=slug)
            
        try:
            with transaction.atomic():
                # 1. Créer le billet
                ticket = Ticket.objects.create(
                    user=request.user,
                    game=game,
                    numbers=selected_numbers,
                    ticket_id=generate_ticket_id(),
                    status='pending',
                    prize_tier='None',  # Default
                    match_count=0
                )
                
                # 2. Déduire du wallet
                user_wallet.balance -= game.ticket_price*len(selected_numbers)
                user_wallet.save()
                
                # 3. Créer le paiement (Transaction record)
                Payment.objects.create(
                    user=request.user,
                    game=game,
                    ticket=ticket,
                    amount=game.ticket_price * len(selected_numbers),
                    payment_type='ticket',
                    payment_method='wallet',
                    status='completed',
                    transaction_id=f"TXN-{ticket.ticket_id}"
                )
                
                 # 4. Mettre à jour les stats du jeu
                game.total_tickets_sold += 1
                game.save()
                
                # 5. Mettre à jour GameFinance
                if hasattr(game, 'finance'):
                    game.finance.update_from_sales(game.ticket_price * len(selected_numbers))
            
            messages.success(request, f"Félicitations! Billet acheté avec succès. ID: {ticket.ticket_id}")
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de l'achat: {str(e)}")
            return redirect('play_game', slug=slug)
            
    # Générer la grille de numéros (1 à number_range)
    number_grid = range(1, game.number_range + 1)
    
    context = {
        'game': game,
        'wallet': user_wallet,
        'number_grid': number_grid,
        'taken_numbers': taken_numbers
    }
    return render(request, 'winning_ticket/play_game.html', context)





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

def is_staff(user):
    """Check if user is staff OR supervisor leader"""
    # Check for direct staff status
    if user.is_staff:
        return True
    # Check for profile-based superuser status
    if hasattr(user, 'profile') and user.profile.is_superuser:
        return True
    return False


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
            
            if is_staff(user):
                return redirect('manage_games')
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')


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
            wallet = Wallet.objects.create(
                user=user,
                balance=1000,
                wallet_type='main'
            )
            wallet.save()
            messages.success(request, "Account created successfully with 1000 dollars in your wallet! You can now login.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return render(request, 'users/register.html', {
                'values': request.POST
            })
            
    return render(request, 'users/register.html')


    return render(request, 'users/register.html')


# ======================================================
# GAME ADMINISTRATION
# ======================================================

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'registration_number', 'contact_email', 'contact_phone', 'address', 'verified']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Legal Name'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Business Reg. Number'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = [
            'name', 
            'description', 
            'company',
            'number_range',
            'ticket_price', 
            'prize_amount',
            'next_draw',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du jeu'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description du jeu'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'number_range': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Plage de numéros'}),
            'ticket_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Prix du billet'}),
            'prize_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Montant du prix'}),
            'next_draw': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
        labels = {
            'name': 'Nom du Jeu',
            'description': 'Description',
            'company': 'Entreprise Organisatrice',
            'number_range': 'Plage de Numéros (1 à X)',
            'ticket_price': 'Prix du Billet',
            'prize_amount': 'Montant Total du Prix',
            'next_draw': 'Date et Heure du Tirage',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate company choices with all active companies
        self.fields['company'].queryset = Company.objects.filter(is_active=True).order_by('name')
        self.fields['company'].empty_label = "-- Sélectionner une entreprise --"

@login_required
@user_passes_test(is_staff)
def admin_dashboard(request):
    """Overall admin dashboard with stats and progression"""
    from django.db.models import Sum, Count
    
    total_revenue = Payment.objects.filter(payment_type='ticket', status='completed').aggregate(total=Sum('amount'))['total'] or 0
    total_tickets = Ticket.objects.count()
    active_games_count = Game.objects.filter(status='active').count()
    total_users = User.objects.count()
    
    recent_transactions = Payment.objects.select_related('user', 'game').order_by('-created_at')[:10]
    active_games = Game.objects.filter(status='active').order_by('-total_tickets_sold')
    ready_games = [g for g in active_games if g.ready_for_draw]
    
    context = {
        'total_revenue': total_revenue,
        'total_tickets': total_tickets,
        'active_games_count': active_games_count,
        'total_users': total_users,
        'recent_transactions': recent_transactions,
        'active_games': active_games,
        'ready_games': ready_games,
    }
    return render(request, 'admins/dashboard.html', context)

@login_required
@user_passes_test(is_staff)
def revenue_report(request):
    """Detailed financial report for platform and games"""
    from django.db.models import Sum
    from principal.models import GameFinance
    
    # Platform totals
    total_stats = GameFinance.objects.aggregate(
        total_sales=Sum('total_sales'),
        total_platform_revenue=Sum('platform_fee_amount'),
        total_organizer_profit=Sum('organizer_profit')
    )
    
    # Breakdown by game
    game_revenues = GameFinance.objects.select_related('game', 'game__company').order_by('-total_sales')
            
    context = {
        'total_sales': total_stats['total_sales'] or 0,
        'platform_revenue': total_stats['total_platform_revenue'] or 0,
        'organizer_profit': total_stats['total_organizer_profit'] or 0,
        'game_revenues': game_revenues
    }
    return render(request, 'admins/revenue_report.html', context)

@login_required
@user_passes_test(is_staff)
def perform_draw(request, game_id):
    """Effectue le tirage au sort pour un jeu terminé"""
    import random
    from django.utils import timezone
    from principal.models import Draw, Winner, Ticket
    
    game = get_object_or_404(Game, id=game_id, status='active')
    
    # 1. Récupérer tous les tickets vendus pour ce jeu
    tickets = Ticket.objects.filter(game=game, status='pending')
    
    if not tickets.exists():
        messages.error(request, "Aucun ticket n'a été vendu pour ce jeu. Tirage impossible.")
        return redirect('admin_dashboard')
    
    # 2. Collecter tous les numéros choisis
    all_chosen_numbers = []
    for t in tickets:
        if isinstance(t.numbers, list):
            all_chosen_numbers.extend(t.numbers)
    
    if not all_chosen_numbers:
        messages.error(request, "Erreur lors de la récupération des numéros.")
        return redirect('admin_dashboard')
        
    # 3. Choisir le numéro gagnant au hasard parmi les numéros choisis
    winning_number = random.choice(all_chosen_numbers)
    
    try:
        with transaction.atomic():
            # 4. Créer l'enregistrement Draw
            draw = Draw.objects.create(
                game=game,
                draw_date=timezone.now(),
                winning_numbers=[winning_number],
                jackpot_amount=game.prize_amount,
                processed=True,
                processed_at=timezone.now(),
                created_by=request.user
            )
            
            # 5. Identifier les tickets gagnants
            winning_tickets = []
            for t in tickets:
                if winning_number in t.numbers:
                    t.status = 'won'
                    t.win_amount = game.prize_amount # Pour l'instant on donne tout au gagnant
                    t.checked = True
                    t.checked_at = timezone.now()
                    t.draw = draw
                    t.save()
                    
                    # Créer Winner record
                    Winner.objects.create(
                        user=t.user,
                        ticket=t,
                        draw=draw,
                        prize_amount=game.prize_amount
                    )
                    winning_tickets.append(t)
                    
                    # Créditer le wallet du gagnant
                    from principal.models import Wallet
                    winner_wallet, _ = Wallet.objects.get_or_create(user=t.user, wallet_type='main')
                    winner_wallet.balance += game.prize_amount
                    winner_wallet.save()
                else:
                    t.status = 'lost'
                    t.checked = True
                    t.checked_at = timezone.now()
                    t.draw = draw
                    t.save()
            
            # 6. Fermer le jeu
            game.status = 'closed'
            game.save()
            
            # Mettre à jour Draw stats
            draw.total_winners = len(winning_tickets)
            draw.total_prize_paid = game.prize_amount if winning_tickets else 0
            draw.jackpot_won = len(winning_tickets) > 0
            draw.save()
            
        messages.success(request, f"Tirage effectué avec succès ! Le numéro gagnant est le {winning_number}.")
        if winning_tickets:
            winner = winning_tickets[0].user
            winner_name = f"{winner.first_name} {winner.last_name}" if winner.first_name else winner.username
            messages.info(request, f"Gagnant identifié : {winner_name} ({winner.email})")
            
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors du tirage : {str(e)}")
        
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_staff)
def manage_games(request):
    """List all games for administration"""
    games = Game.objects.all().order_by('-created_at')
    return render(request, 'admins/manage_games.html', {'games': games})

@login_required
@user_passes_test(is_staff)
def create_game(request):
    if request.method == 'POST':
        form = GameForm(request.POST)
        if form.is_valid():
            game = form.save(commit=False)
            game.status = 'active'  # Auto-activate for now
            game.save()
            messages.success(request, "Jeu créé avec succès! Un enregistrement GameFinance a été créé automatiquement.")
            return redirect('manage_games')
    else:
        form = GameForm()
    
    return render(request, 'admins/game_form.html', {'form': form, 'title': 'Créer un Jeu'})

@login_required
@user_passes_test(is_staff)
def edit_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        form = GameForm(request.POST, instance=game)
        if form.is_valid():
            form.save()
            messages.success(request, "Game updated successfully!")
            return redirect('manage_games')
    else:
        form = GameForm(instance=game)
    
    return render(request, 'admins/game_form.html', {'form': form, 'title': 'Edit Game', 'game': game})

@login_required
@user_passes_test(is_staff)
def delete_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        game.delete()
        messages.success(request, "Game deleted successfully!")
        return redirect('manage_games')
    return redirect('manage_games')


# ======================================================
# COMPANY ADMINISTRATION
# ======================================================

@login_required
@user_passes_test(is_staff)
def manage_companies(request):
    companies = Company.objects.all().order_by('name')
    return render(request, 'admins/manage_companies.html', {'companies': companies})

@login_required
@user_passes_test(is_staff)
def create_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Company created successfully!")
            return redirect('manage_companies')
    else:
        form = CompanyForm()
    return render(request, 'admins/company_form.html', {'form': form, 'title': 'Create Company'})

@login_required
@user_passes_test(is_staff)
def edit_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company updated successfully!")
            return redirect('manage_companies')
    else:
        form = CompanyForm(instance=company)
    return render(request, 'admins/company_form.html', {'form': form, 'title': 'Edit Company'})

@login_required
@user_passes_test(is_staff)
def delete_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        company.delete()
        messages.success(request, "Company deleted successfully!")
        return redirect('manage_companies')
    return redirect('manage_companies')


@login_required
def dashboard(request):
    """
    User dashboard displaying stats and recent tickets.
    """
    user = request.user
    
    # Get user's wallet
    wallet, created = Wallet.objects.get_or_create(
        user=user, 
        wallet_type='main',
        defaults={'balance': 0}
    )
    
    # Get recent tickets (last 5)
    recent_tickets = Ticket.objects.filter(user=user).select_related('game').order_by('-created_at')[:5]
    
    # Calculate stats
    total_tickets = Ticket.objects.filter(user=user).count()
    active_tickets = Ticket.objects.filter(user=user, status='pending').count()
    total_won = Ticket.objects.filter(user=user, status='won').aggregate(models.Sum('win_amount'))['win_amount__sum'] or 0
    unclaimed_prizes = Ticket.objects.filter(user=user, status='won', checked=False).count()
    
    context = {
        'wallet': wallet,
        'recent_tickets': recent_tickets,
        'total_tickets': total_tickets,
        'active_tickets': active_tickets,
        'total_won': total_won,
        'unclaimed_prizes': unclaimed_prizes,
    }
    return render(request, 'users/dashboard.html', context)
