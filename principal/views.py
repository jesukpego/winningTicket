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
from django.utils.translation import activate, gettext as _  # i18n
from django.conf import settings
from .models import Game, Company, Wallet, Ticket, Payment, Winner, Draw

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
    Page d'accueil avec les jeux en vedette et les statistiques.
    """
    featured_games = Game.objects.filter(status='active').order_by('-created_at')[:3]
    recent_winners = Winner.objects.select_related('user', 'draw', 'draw__game').order_by('-draw__draw_date')[:5]
    
    from django.db.models import Sum
    total_jackpot = Game.objects.filter(status='active').aggregate(Sum('prize_amount'))['prize_amount__sum'] or 0
    total_winners_count = Winner.objects.count()
    
    context = {
        'featured_games': featured_games,
        'recent_winners': recent_winners,
        'total_jackpot': total_jackpot,
        'total_winners_count': total_winners_count,
    }
    return render(request, 'winning_ticket/index.html', context)

# ======================================================
# PAGES HTML SIMPLES
# ======================================================

def accueil(request):
    return render(request, 'winning_ticket/indx.html')

def faq(request):
    return render(request, 'winning_ticket/faq.html')

# ======================================================
# LOGIQUE DES JEUX
# ======================================================

def games(request):
    """
    Page listant les jeux disponibles avec filtres optionnels.
    """
    games = Game.objects.filter(status='active').select_related('company').order_by('ticket_price')
    companies = Company.objects.filter(is_active=True, games__status='active').distinct()
    
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
    """Génère un ID de billet aléatoire de 10 caractères"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


@login_required
def play_game(request, slug):
    """
    Page pour jouer à un jeu spécifique.
    Gère l'affichage de la grille et l'achat de billets.
    """
    game = get_object_or_404(Game, slug=slug, status='active')
    
    user_wallet, created = Wallet.objects.get_or_create(
        user=request.user, 
        wallet_type='main',
        defaults={'balance': 0}
    )
    
    taken_numbers = set()
    existing_tickets = Ticket.objects.filter(game=game)
    for t in existing_tickets:
        if isinstance(t.numbers, list):
            taken_numbers.update(t.numbers)

    if request.method == 'POST':
        selected_numbers_raw = request.POST.getlist('selected_numbers')

        selected_numbers = [int(n) for n in selected_numbers_raw if n.isdigit()]
        
        if not selected_numbers:
            messages.error(request, _("Veuillez sélectionner au moins un numéro."))
            return redirect('play_game', slug=slug)

        for num in selected_numbers:
            if num in taken_numbers:
                messages.error(request, _("Le numéro %(num)s a déjà été acheté par un autre joueur.") % {'num': num})
                return redirect('play_game', slug=slug)

        if user_wallet.balance < game.ticket_price:
            messages.error(request, _("Solde insuffisant. Veuillez recharger votre portefeuille."))
            return redirect('play_game', slug=slug)
            
        try:
            with transaction.atomic():
                draw_date = game.next_draw or timezone.now()
                
                ticket = Ticket.objects.create(
                    user=request.user,
                    game=game,
                    numbers=selected_numbers,
                    ticket_id=generate_ticket_id(),
                    draw_date=draw_date,
                    status='pending',
                    prize_tier='None',
                    match_count=0
                )
                
                user_wallet.balance -= game.ticket_price
                user_wallet.save()
                
                Payment.objects.create(
                    user=request.user,
                    game=game,
                    ticket=ticket,
                    amount=game.ticket_price,
                    payment_type='ticket',
                    payment_method='wallet',
                    status='completed',
                    transaction_id=f"TXN-{ticket.ticket_id}"
                )
                
                game.total_tickets_sold += 1
                game.save()
                
                if hasattr(game, 'finance'):
                    game.finance.update_from_sales(game.ticket_price)
            
            messages.success(request, _("Félicitations! Votre billet a été acheté avec succès. ID: %(id)s") % {'id': ticket.ticket_id})
            return redirect('my_tickets')
            
        except Exception as e:
            messages.error(request, _("Une erreur est survenue lors de l'achat : %(err)s") % {'err': str(e)})
            return redirect('play_game', slug=slug)
            
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
    context = {
        'game_id': game_id,
    }
    return render(request, 'winning_ticket/game_detail.html', context)


def buy_ticket(request):
    return render(request, 'winning_ticket/buy_ticket.html')


@login_required
def my_tickets(request):
    """
    Affiche les billets achetés par l'utilisateur connecté.
    """
    user = request.user
    wallet, created = Wallet.objects.get_or_create(
        user=user, 
        wallet_type='main',
        defaults={'balance': 0}
    )
    
    tickets = Ticket.objects.filter(user=user).select_related('game').order_by('-created_at')
    
    total_won = tickets.filter(status='won').aggregate(models.Sum('win_amount'))['win_amount__sum'] or 0
    
    context = {
        'wallet': wallet,
        'tickets': tickets,
        'total_tickets': tickets.count(),
        'active_tickets': tickets.filter(status='pending').count(),
        'total_won': total_won,
        'unclaimed_prizes': tickets.filter(status='won', checked=False).count(),
    }
    return render(request, 'winning_ticket/my_tickets.html', context)


def results(request):
    recent_draws = Draw.objects.select_related('game').order_by('-draw_date')[:20]
    return render(request, 'winning_ticket/results.html', {'recent_draws': recent_draws})


def winners(request):
    from django.db.models import Sum
    winners_list = Winner.objects.select_related('user', 'draw', 'draw__game').order_by('-draw__draw_date')
    
    total_gains = Winner.objects.aggregate(total=Sum('prize_amount'))['total'] or 0
    total_winners_count = Winner.objects.count()
    last_win = winners_list.first()
    
    context = {
        'winners': winners_list[:30],
        'total_gains': total_gains,
        'total_winners_count': total_winners_count,
        'last_win_amount': last_win.prize_amount if last_win else 0
    }
    return render(request, 'winning_ticket/winners.html', context)


# ======================================================
# AUTHENTIFICATION & DASHBOARD
# ======================================================

def is_staff(user):
    if user.is_staff:
        return True
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
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(1209600)
            
            messages.success(request, _("Bon retour, %(user)s!") % {'user': user.username})
            
            if is_staff(user):
                return redirect('manage_games')
            
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, _("Nom d'utilisateur ou mot de passe incorrect."))
            
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, _("Vous avez été déconnecté avec succès."))
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        data = request.POST
        if data.get('password1') != data.get('password2'):
            messages.error(request, _("Les mots de passe ne correspondent pas !"))
        elif User.objects.filter(username=data.get('username')).exists():
            messages.error(request, _("Ce nom d'utilisateur est déjà pris !"))
        else:
            try:
                user = User.objects.create_user(
                    username=data.get('username'),
                    email=data.get('email'),
                    password=data.get('password1'),
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name')
                )
                Wallet.objects.create(user=user, balance=1000, wallet_type='main')
                messages.success(request, _("Votre compte a été créé avec succès ! Vous avez reçu 1000 unités de bienvenue."))
                return redirect('login')
            except Exception as e:
                messages.error(request, _("Une erreur est survenue lors de la création du compte : %(e)s") % {'e': e})
            
    return render(request, 'users/register.html')


# ======================================================
# ADMINISTRATION (GESTION DES JEUX ET ENTREPRISES)
# ======================================================

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'registration_number', 'contact_email', 'contact_phone', 'address', 'verified']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all'}),
            'registration_number': forms.TextInput(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all'}),
            'contact_email': forms.EmailInput(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all'}),
            'contact_phone': forms.TextInput(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all'}),
            'address': forms.Textarea(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all', 'rows': 3}),
        }

class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['name', 'description', 'company', 'number_range', 'ticket_price', 'prize_amount', 'next_draw']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all'}),
            'description': forms.Textarea(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all', 'rows': 3}),
            'company': forms.Select(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all'}),
            'number_range': forms.NumberInput(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all'}),
            'ticket_price': forms.NumberInput(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-10 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all'}),
            'prize_amount': forms.NumberInput(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-10 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all'}),
            'next_draw': forms.DateTimeInput(attrs={'class': 'w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-yellow-400/50 transition-all', 'type': 'datetime-local'}),
        }
        labels = {
            'name': _('Nom du Jeu'),
            'description': _('Description'),
            'company': _('Entreprise'),
            'number_range': _('Plage de numéros'),
            'ticket_price': _('Prix du ticket'),
            'prize_amount': _('Montant du prix'),
            'next_draw': _('Prochain tirage'),
        }
        def clean_name(self):
               name = self.cleaned_data.get('name')
       
               # Vérifie si un jeu avec le même nom existe déjà
               if Game.objects.filter(name__iexact=name).exists():
                   raise ValidationError("Un jeu avec ce nom existe déjà.")
       
               return name

@login_required
@user_passes_test(is_staff)
def admin_dashboard(request):
    from django.db.models import Sum
    active_games = Game.objects.filter(status='active').order_by('-created_at')
    
    total_revenue = Payment.objects.filter(payment_type='ticket', status='completed').aggregate(total=Sum('amount'))['total'] or 0
    total_tickets = Ticket.objects.count()
    total_users = User.objects.count()
    active_games_count = active_games.count()

    context = {
        'stats': {
            'total_revenue': f"{total_revenue:,.2f}",
            'total_tickets': f"{total_tickets:,}",
            'total_users': f"{total_users:,}",
            'active_games': active_games_count,
        },
        'active_games': active_games,
        'recent_transactions': Payment.objects.select_related('user', 'game').order_by('-created_at')[:10],
    }
    return render(request, 'admins/dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def perform_draw(request, game_id):
    game = get_object_or_404(Game, id=game_id, status='active')
    tickets = Ticket.objects.filter(game=game, status='pending')
    
    if not tickets.exists():
        messages.error(request, _("Aucun ticket n'a été vendu pour ce jeu. Tirage impossible."))
        return redirect('admin_dashboard')
    
    all_numbers = []
    for t in tickets:
        if t.numbers:
            all_numbers.extend(t.numbers)
    
    winning_number = random.choice(all_numbers)
    
    try:
        with transaction.atomic():
            draw = Draw.objects.create(
                game=game,
                draw_date=timezone.now(),
                winning_numbers=[winning_number],
                jackpot_amount=game.prize_amount,
                processed=True,
                created_by=request.user
            )
            
            winners_count = 0
            for t in tickets:
                if winning_number in t.numbers:
                    t.status = 'won'
                    t.win_amount = game.prize_amount
                    t.checked = True
                    t.draw = draw
                    t.save()
                    
                    Winner.objects.create(
                        user=t.user,
                        ticket=t,
                        draw=draw,
                        prize_amount=game.prize_amount
                    )
                    
                    winner_wallet, _ = Wallet.objects.get_or_create(user=t.user, wallet_type='main')
                    winner_wallet.balance += game.prize_amount
                    winner_wallet.save()
                    winners_count += 1
                else:
                    t.status = 'lost'
                    t.checked = True
                    t.draw = draw
                    t.save()
            
            game.status = 'closed'
            game.save()
            
            draw.total_winners = winners_count
            draw.save()
            
        messages.success(request, _("Le tirage a été effectué avec succès ! Le numéro gagnant est le %(num)s.") % {'num': winning_number})
    except Exception as e:
        messages.error(request, _("Une erreur est survenue lors du tirage : %(e)s") % {'e': str(e)})
        
    return redirect('admin_dashboard')


@login_required
@user_passes_test(is_staff)
def manage_games(request):
    games = Game.objects.all().order_by('-created_at')
    return render(request, 'admins/manage_games.html', {'games': games})


@login_required
@user_passes_test(is_staff)
def create_game(request):
    if request.method == 'POST':
        form = GameForm(request.POST)
        if form.is_valid():
            game = form.save(commit=False)
            game.status = 'active'
            game.save()
            messages.success(request, _("Le jeu a été créé avec succès !"))
            return redirect('manage_games')
    else:
        form = GameForm()
    return render(request, 'admins/game_form.html', {'form': form, 'title': _('Créer un nouveau jeu')})


@login_required
@user_passes_test(is_staff)
def edit_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        form = GameForm(request.POST, instance=game)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le jeu a été mis à jour avec succès !"))
            return redirect('manage_games')
    else:
        form = GameForm(instance=game)
    return render(request, 'admins/game_form.html', {'form': form, 'title': _('Modifier le jeu')})


@login_required
@user_passes_test(is_staff)
def delete_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        game.delete()
        messages.success(request, _("Le jeu a été supprimé."))
        return redirect('manage_games')
    return render(request, 'admins/game_confirm_delete.html', {'game': game})


@login_required
@user_passes_test(is_staff)
def manage_companies(request):
    companies = Company.objects.all().order_by('name')
    return render(request, 'admins/manage_companies.html', {'companies': companies})


@login_required
@user_passes_test(is_staff)
def revenue_report(request):
    from django.db.models import Sum
    
    # Global statistics
    payments = Payment.objects.filter(payment_type='ticket', status='completed').select_related('user', 'game').order_by('-created_at')
    total_sales = payments.aggregate(total=Sum('amount'))['total'] or 0
    platform_revenue = (total_sales * 20) / 100  # 20% platform fee
    
    # Group by game for breakdown
    game_revenues = []
    active_games = Game.objects.all().select_related('company')
    
    total_organizer_profit = 0
    
    for game in active_games:
        game_sales = game.ticket_price * game.total_tickets_sold
        game_platform_fee = (game_sales * game.platform_fee_percent) / 100
        # In this model, profit is what remains for organizer after prize and fee
        # Let's use the property from model directly if possible or calculate here
        game_profit = game_sales - game_platform_fee - game.prize_amount
        
        if game_sales > 0:
            game_revenues.append({
                'game': game,
                'total_sales': game_sales,
                'platform_fee_amount': game_platform_fee,
                'organizer_profit': game_profit
            })
            total_organizer_profit += game_profit
            
    context = {
        'payments': payments,
        'total_sales': total_sales,
        'platform_revenue': platform_revenue,
        'organizer_profit': total_organizer_profit,
        'game_revenues': game_revenues,
    }
    return render(request, 'admins/revenue_report.html', context)


@login_required
def dashboard(request):
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(user=user, wallet_type='main', defaults={'balance': 0})
    recent_tickets = Ticket.objects.filter(user=user).select_related('game').order_by('-created_at')[:5]
    
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


# ======================================================
# LANGUAGE SWITCHER
# ======================================================

def set_language(request):
    """
    Change la préférence de langue de l'utilisateur.
    """
    if request.method == 'POST':
        language_code = request.POST.get('language')
        
        if language_code and language_code in [lang[0] for lang in settings.LANGUAGES]:
            activate(language_code)
            request.session['django_language'] = language_code
            
            next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
            response = redirect(next_url)
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language_code)
            return response
            
    return redirect('home')
# À RAJOUTER À LA FIN DE principal/views.py

@login_required
@user_passes_test(is_staff)
def create_company(request):
    """
    Vue pour créer une nouvelle entreprise (demandée par urls.py)
    """
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'entreprise a été créée avec succès !"))
            return redirect('manage_companies')
    else:
        form = CompanyForm()
    return render(request, 'admins/company_form.html', {'form': form, 'title': _("Créer une Entreprise")})

@login_required
@user_passes_test(is_staff)
def edit_company(request, company_id):
    """
    Vue pour modifier une entreprise existante
    """
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'entreprise a été mise à jour !"))
            return redirect('manage_companies')
    else:
        form = CompanyForm(instance=company)
    return render(request, 'admins/company_form.html', {'form': form, 'title': _("Modifier l'Entreprise")})

@login_required
@user_passes_test(is_staff)
def delete_company(request, company_id):
    """
    Vue pour supprimer une entreprise
    """
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        company.delete()
        messages.success(request, _("L'entreprise a été supprimée."))
        return redirect('manage_companies')
    return render(request, 'admins/company_confirm_delete.html', {'company': company})