from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    UserProfile, Company, CompanyUser, Game, Ticket, Draw, Winner,
    Payment, GameFinance, Syndicate, SyndicateMember, AuditLog, Wallet
)


# ============================================================================
# USERPROFILE ADMIN
# ============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Interface d'administration pour les profils utilisateurs."""
    
    list_display = (
        'user_link', 'email', 'total_spent_display', 'total_won_display',
        'games_played', 'age_verified', 'created_at'
    )
    list_filter = (
        'age_verified', 'email_notifications', 'sms_notifications',
        'created_at', 'updated_at'
    )
    search_fields = ('user__username', 'user__email')
    readonly_fields = (
        'total_spent', 'total_won', 'games_played',
        'net_profit', 'win_ratio', 'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('Informations de Base', {
            'fields': ('user',)
        }),
        ('Vérification', {
            'fields': ('age_verified', 'verification_date')
        }),
        ('Préférences de Notification', {
            'fields': ('email_notifications', 'sms_notifications')
        }),
        ('Statistiques', {
            'fields': (
                'total_spent', 'total_won', 'games_played',
                'net_profit', 'win_ratio'
            ),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_users']
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Utilisateur'
    
    def email(self, obj):
        """Email de l'utilisateur."""
        return obj.user.email
    email.short_description = 'Email'
    
    def total_spent_display(self, obj):
        """Affichage des dépenses."""
        return format_html('${:,.2f}', obj.total_spent)
    total_spent_display.short_description = 'Total Dépensé'
    
    def total_won_display(self, obj):
        """Affichage des gains."""
        return format_html(
            '<span style="color: green; font-weight: bold;">${:,.2f}</span>',
            obj.total_won
        )
    total_won_display.short_description = 'Total Gagné'
    
    def verify_users(self, request, queryset):
        """Action pour vérifier les utilisateurs."""
        from django.utils import timezone
        updated = queryset.update(age_verified=True, verification_date=timezone.now())
        self.message_user(request, f'{updated} utilisateurs vérifiés.')
    verify_users.short_description = 'Vérifier les utilisateurs sélectionnés'


# ============================================================================
# COMPANY & COMPANYUSER ADMIN
# ============================================================================

class CompanyUserInline(admin.TabularInline):
    """Inline pour les utilisateurs d'une entreprise."""
    model = CompanyUser
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('user', 'role', 'can_create_games', 'can_view_finances', 'created_at')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Interface d'administration pour les entreprises."""
    
    list_display = (
        'name', 'registration_number', 'contact_email', 'verified_status',
        'is_active', 'balance_display', 'total_games_count', 'active_games_count', 'created_at'
    )
    list_filter = ('verified', 'is_active', 'created_at')
    search_fields = ('name', 'registration_number', 'contact_email')
    readonly_fields = ('created_at', 'updated_at', 'verified_at', 'total_games_count', 'active_games_count')
    inlines = [CompanyUserInline]
    
    fieldsets = (
        ('Informations de Base', {
            'fields': ('name', 'registration_number', 'contact_email', 'contact_phone')
        }),
        ('Adresse', {
            'fields': ('address',)
        }),
        ('Vérification', {
            'fields': ('verified', 'verified_at', 'is_active')
        }),
        ('Finances', {
            'fields': ('balance',)
        }),
        ('Statistiques', {
            'fields': ('total_games_count', 'active_games_count'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_companies', 'activate_companies', 'deactivate_companies']
    
    def verified_status(self, obj):
        """Statut de vérification avec icône."""
        if obj.verified:
            return format_html('<span style="color: green;">✓ Vérifié</span>')
        return format_html('<span style="color: red;">✗ Non vérifié</span>')
    verified_status.short_description = 'Statut'
    
    def balance_display(self, obj):
        """Affichage du solde."""
        color = 'green' if obj.balance > 0 else 'red' if obj.balance < 0 else 'black'
        return format_html(
            '<span style="color: {};">${:,.2f}</span>',
            color, obj.balance
        )
    balance_display.short_description = 'Solde'
    
    def total_games_count(self, obj):
        """Total des jeux."""
        return obj.total_games
    total_games_count.short_description = 'Total Jeux'
    
    def active_games_count(self, obj):
        """Jeux actifs."""
        return obj.active_games
    active_games_count.short_description = 'Jeux Actifs'
    
    def verify_companies(self, request, queryset):
        """Vérifier les entreprises."""
        from django.utils import timezone
        updated = queryset.update(verified=True, verified_at=timezone.now())
        self.message_user(request, f'{updated} entreprises vérifiées.')
    verify_companies.short_description = 'Vérifier les entreprises sélectionnées'
    
    def activate_companies(self, request, queryset):
        """Activer les entreprises."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} entreprises activées.')
    activate_companies.short_description = 'Activer'
    
    def deactivate_companies(self, request, queryset):
        """Désactiver les entreprises."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} entreprises désactivées.')
    deactivate_companies.short_description = 'Désactiver'


@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    """Interface d'administration pour les utilisateurs d'entreprise."""
    
    list_display = ('user', 'company', 'role', 'can_create_games', 'can_view_finances', 'created_at')
    list_filter = ('role', 'can_create_games', 'can_view_finances', 'created_at')
    search_fields = ('user__username', 'company__name')
    readonly_fields = ('created_at', 'updated_at')


# ============================================================================
# GAME ADMIN
# ============================================================================

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Interface d'administration pour les jeux."""
    
    list_display = (
        'name', 'company_display', 'status_display', 'ticket_price_display',
        'prize_amount_display', 'total_sales_display', 'created_at'
    )
    list_filter = ('status', 'created_at', 'company')
    search_fields = ('name', 'slug', 'description')
    readonly_fields = (
        'slug', 'total_sales_display', 'platform_fee_amount', 'organizer_profit',
        'created_at', 'updated_at', 'published_at'
    )
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Informations de Base', {
            'fields': ('name', 'slug', 'description', 'status')
        }),
        ('Entreprise Organisatrice', {
            'fields': ('company',)
        }),
        ('Configuration du Jeu', {
            'fields': (
                'min_numbers', 'max_numbers', 'number_range',
                'has_powerball', 'powerball_range'
            )
        }),
        ('Tarification', {
            'fields': ('ticket_price', 'prize_amount', 'platform_fee_percent')
        }),
        ('Timing', {
            'fields': ('next_draw', 'ticket_sale_end')
        }),
        ('Statistiques & Finances', {
            'fields': ('total_tickets_sold', 'total_sales_display', 'platform_fee_amount', 'organizer_profit'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['publish_games', 'close_games', 'activate_games']
    
    def company_display(self, obj):
        """Affichage de l'entreprise."""
        if obj.company:
            return format_html('<span style="color: purple;">🏛️ {}</span>', obj.company.name)
        return format_html('<span style="color: red;">Aucune entreprise</span>')
    company_display.short_description = 'Entreprise'
    
    def status_display(self, obj):
        """Affichage du statut avec couleur."""
        colors = {
            'draft': 'gray',
            'pending': 'orange',
            'active': 'green',
            'closed': 'blue',
            'canceled': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Statut'
    
    def ticket_price_display(self, obj):
        """Affichage du prix du billet."""
        return format_html('${:.2f}', obj.ticket_price)
    ticket_price_display.short_description = 'Prix Billet'
    
    def prize_amount_display(self, obj):
        """Affichage du prix total."""
        return format_html(
            '<span style="color: gold; font-weight: bold;">${:,.2f}</span>',
            obj.prize_amount
        )
    prize_amount_display.short_description = 'Prix Total'
    
    def total_sales_display(self, obj):
        """Affichage du total des ventes."""
        total = obj.total_sales
        return format_html('${:,.2f}', total)
    total_sales_display.short_description = 'Ventes Totales'
    
    def publish_games(self, request, queryset):
        """Publier les jeux."""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} jeux publiés.')
    publish_games.short_description = 'Publier les jeux sélectionnés'
    
    def close_games(self, request, queryset):
        """Fermer les jeux."""
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} jeux fermés.')
    close_games.short_description = 'Fermer'
    
    def activate_games(self, request, queryset):
        """Activer les jeux."""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} jeux activés.')
    activate_games.short_description = 'Activer'


# ============================================================================
# TICKET ADMIN
# ============================================================================

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Interface d'administration pour les billets."""
    
    list_display = (
        'ticket_id', 'game', 'user_link', 'numbers_display_short',
        'status_display', 'win_amount_display', 'created_at'
    )
    list_filter = ('status', 'checked', 'created_at', 'draw_date')
    search_fields = ('ticket_id', 'user__username')
    readonly_fields = (
        'ticket_id', 'match_count', 'has_powerball_match', 'prize_tier',
        'win_amount', 'checked', 'checked_at', 'created_at'
    )
    
    fieldsets = (
        ('Informations du Billet', {
            'fields': ('ticket_id', 'game', 'user', 'draw', 'draw_date')
        }),
        ('Numéros', {
            'fields': ('numbers', 'powerball')
        }),
        ('Statut & Résultats', {
            'fields': (
                'status', 'match_count', 'has_powerball_match',
                'prize_tier', 'win_amount'
            )
        }),
        ('Vérification', {
            'fields': ('checked', 'checked_at'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['check_winners', 'refund_tickets']
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Utilisateur'
    
    def numbers_display_short(self, obj):
        """Affichage court des numéros."""
        nums = ', '.join(str(n) for n in obj.numbers)
        if obj.powerball:
            nums += f' + PB:{obj.powerball}'
        return nums[:40] + '...' if len(nums) > 40 else nums
    numbers_display_short.short_description = 'Numéros'
    
    def status_display(self, obj):
        """Affichage du statut."""
        colors = {
            'pending': 'orange',
            'won': 'green',
            'lost': 'red',
            'refunded': 'blue'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Statut'
    
    def win_amount_display(self, obj):
        """Affichage du montant gagné."""
        if obj.win_amount and obj.win_amount > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">${:,.2f}</span>',
                obj.win_amount
            )
        return '-'
    win_amount_display.short_description = 'Montant Gagné'
    
    def check_winners(self, request, queryset):
        """Vérifier les gagnants."""
        count = 0
        for ticket in queryset:
            if ticket.draw:
                ticket.check_win(ticket.draw)
                count += 1
        self.message_user(request, f'{count} billets vérifiés.')
    check_winners.short_description = 'Vérifier les gagnants'
    
    def refund_tickets(self, request, queryset):
        """Rembourser les billets."""
        updated = queryset.update(status='refunded')
        self.message_user(request, f'{updated} billets remboursés.')
    refund_tickets.short_description = 'Rembourser'


# ============================================================================
# DRAW ADMIN
# ============================================================================

class WinnerInline(admin.TabularInline):
    """Inline pour les gagnants d'un tirage."""
    model = Winner
    extra = 0
    readonly_fields = ('user', 'ticket', 'prize_tier', 'prize_amount', 'claimed', 'paid')
    can_delete = False
    fields = ('user', 'ticket', 'prize_tier', 'prize_amount', 'claimed', 'paid')


@admin.register(Draw)
class DrawAdmin(admin.ModelAdmin):
    """Interface d'administration pour les tirages."""
    
    list_display = (
        'game', 'draw_number', 'draw_date', 'winning_numbers_short',
        'prize_pool_display', 'processed', 'has_jackpot_winner'
    )
    list_filter = ('processed', 'draw_date', 'game')
    search_fields = ('game__name', 'draw_number')
    readonly_fields = (
        'draw_number', 'processed', 'processed_at', 'total_tickets',
        'total_winners', 'has_jackpot_winner', 'created_at'
    )
    inlines = [WinnerInline]
    
    fieldsets = (
        ('Informations du Tirage', {
            'fields': ('game', 'draw_number', 'draw_date', 'prize_pool')
        }),
        ('Numéros Gagnants', {
            'fields': ('winning_numbers', 'winning_powerball')
        }),
        ('Traitement', {
            'fields': ('processed', 'processed_at')
        }),
        ('Statistiques', {
            'fields': ('total_tickets', 'total_winners', 'has_jackpot_winner'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['process_draws', 'generate_random_numbers']
    
    def winning_numbers_short(self, obj):
        """Affichage court des numéros gagnants."""
        if obj.winning_numbers:
            nums = ', '.join(str(n) for n in obj.winning_numbers)
            if obj.winning_powerball:
                nums += f' + PB:{obj.winning_powerball}'
            return nums
        return 'Non défini'
    winning_numbers_short.short_description = 'Numéros Gagnants'
    
    def prize_pool_display(self, obj):
        """Affichage de la cagnotte."""
        return format_html(
            '<span style="color: gold; font-weight: bold;">${:,.2f}</span>',
            obj.prize_pool
        )
    prize_pool_display.short_description = 'Cagnotte'
    
    def has_jackpot_winner(self, obj):
        """Indicateur de gagnant du jackpot."""
        # Check if there's a jackpot winner
        has_winner = obj.winners.filter(prize_tier__icontains='Match').exists()
        if has_winner:
            return format_html('<span style="color: green;">✓ Oui</span>')
        return format_html('<span style="color: gray;">✗ Non</span>')
    has_jackpot_winner.short_description = 'Jackpot Gagné'
    
    def process_draws(self, request, queryset):
        """Traiter les tirages."""
        count = 0
        for draw in queryset.filter(processed=False):
            draw.process_draw()
            count += 1
        self.message_user(request, f'{count} tirages traités.')
    process_draws.short_description = 'Traiter les tirages sélectionnés'
    
    def generate_random_numbers(self, request, queryset):
        """Générer des numéros aléatoires."""
        import random
        count = 0
        for draw in queryset.filter(processed=False):
            if not draw.winning_numbers:
                numbers = sorted(random.sample(range(1, draw.game.number_range + 1), draw.game.max_numbers))
                draw.winning_numbers = numbers
                if draw.game.has_powerball:
                    draw.winning_powerball = random.randint(1, draw.game.powerball_range)
                draw.save()
                count += 1
        self.message_user(request, f'{count} tirages avec numéros générés.')
    generate_random_numbers.short_description = 'Générer numéros aléatoires'


# ============================================================================
# WINNER ADMIN
# ============================================================================

@admin.register(Winner)
class WinnerAdmin(admin.ModelAdmin):
    """Interface d'administration pour les gagnants."""
    
    list_display = (
        'user_link', 'draw', 'prize_tier_display', 'prize_amount_display',
        'claimed', 'paid', 'net_amount_display', 'created_at'
    )
    list_filter = ('claimed', 'paid', 'prize_tier', 'created_at')
    search_fields = ('user__username', 'ticket__ticket_id')
    readonly_fields = (
        'net_amount_display', 'tax_percentage_calculated',
        'days_since_win', 'created_at', 'claimed_at', 'paid_at'
    )
    
    fieldsets = (
        ('Informations du Gagnant', {
            'fields': ('user', 'ticket', 'draw')
        }),
        ('Prix', {
            'fields': (
                'prize_tier', 'prize_amount', 'tax_percentage',
                'tax_withheld', 'net_amount_display'
            )
        }),
        ('Réclamation & Paiement', {
            'fields': (
                'claimed', 'claimed_at', 'paid', 'paid_at',
                'payout_method', 'payout_reference'
            )
        }),
        ('Statistiques', {
            'fields': ('tax_percentage_calculated', 'days_since_win'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_claimed', 'process_payments']
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Utilisateur'
    
    def prize_tier_display(self, obj):
        """Affichage du niveau de prix."""
        colors = {
            'jackpot': 'gold',
            'second': 'silver',
            'third': '#cd7f32',
        }
        # Simple color based on prize amount
        color = 'gold' if obj.prize_amount > 10000 else 'silver' if obj.prize_amount > 1000 else 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.prize_tier
        )
    prize_tier_display.short_description = 'Niveau'
    
    def prize_amount_display(self, obj):
        """Affichage du montant du prix."""
        return format_html(
            '<span style="color: green; font-weight: bold;">${:,.2f}</span>',
            obj.prize_amount
        )
    prize_amount_display.short_description = 'Montant Prix'
    
    def net_amount_display(self, obj):
        """Affichage du montant net."""
        net = obj.net_amount()
        return format_html('${:,.2f}', net)
    net_amount_display.short_description = 'Montant Net'
    
    def tax_percentage_calculated(self, obj):
        """Calcul du pourcentage de taxe."""
        return obj.tax_percentage_calculated()
    tax_percentage_calculated.short_description = '% Taxe Calculé'
    
    def days_since_win(self, obj):
        """Jours depuis le gain."""
        return obj.days_since_win()
    days_since_win.short_description = 'Jours Depuis Gain'
    
    def mark_as_claimed(self, request, queryset):
        """Marquer comme réclamé."""
        count = 0
        for winner in queryset:
            winner.claim_prize()
            count += 1
        self.message_user(request, f'{count} prix réclamés.')
    mark_as_claimed.short_description = 'Marquer comme réclamé'
    
    def process_payments(self, request, queryset):
        """Traiter les paiements."""
        count = 0
        for winner in queryset.filter(claimed=True, paid=False):
            success = winner.process_payment(payout_method='wallet', reference=f'ADMIN-{winner.id}')
            if success:
                count += 1
        self.message_user(request, f'{count} paiements traités.')
    process_payments.short_description = 'Traiter les paiements'


# ============================================================================
# PAYMENT ADMIN
# ============================================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Interface d'administration pour les paiements."""
    
    list_display = (
        'transaction_id', 'user_link', 'payment_type_display',
        'amount_display', 'status_display', 'payment_method',
        'created_at'
    )
    list_filter = ('status', 'payment_type', 'payment_method', 'created_at')
    search_fields = ('transaction_id', 'gateway_transaction_id', 'user__username')
    readonly_fields = (
        'transaction_id', 'net_amount', 'processing_fee',
        'age_in_minutes', 'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('Informations du Paiement', {
            'fields': ('transaction_id', 'user', 'payment_type', 'internal_reference')
        }),
        ('Montants', {
            'fields': (
                'amount', 'processing_fee', 'net_amount'
            )
        }),
        ('Statut & Méthode', {
            'fields': (
                'status', 'payment_method',
                'gateway_transaction_id', 'gateway_response'
            )
        }),
        ('Relations', {
            'fields': ('ticket', 'game'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'age_in_minutes'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = 'Utilisateur'
    
    def payment_type_display(self, obj):
        """Affichage du type de paiement."""
        colors = {
            'ticket': 'blue',
            'payout': 'green',
            'refund': 'orange',
            'commission': 'purple',
            'deposit': 'teal',
            'withdrawal': 'brown'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.payment_type, 'black'),
            obj.get_payment_type_display()
        )
    payment_type_display.short_description = 'Type'
    
    def amount_display(self, obj):
        """Affichage du montant."""
        return format_html('${:,.2f}', obj.amount)
    amount_display.short_description = 'Montant'
    
    def status_display(self, obj):
        """Affichage du statut."""
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'canceled': 'gray',
            'refunded': 'purple'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Statut'
    
    def age_in_minutes(self, obj):
        """Âge du paiement en minutes."""
        return obj.age_in_minutes()
    age_in_minutes.short_description = 'Âge (minutes)'
    
    def mark_as_completed(self, request, queryset):
        """Marquer comme complété."""
        count = 0
        for payment in queryset.filter(status='pending'):
            payment.mark_as_completed()
            count += 1
        self.message_user(request, f'{count} paiements marqués comme complétés.')
    mark_as_completed.short_description = 'Marquer comme complété'
    
    def mark_as_failed(self, request, queryset):
        """Marquer comme échoué."""
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} paiements marqués comme échoués.')
    mark_as_failed.short_description = 'Marquer comme échoué'


# ============================================================================
# GAMEFINANCE ADMIN
# ============================================================================

@admin.register(GameFinance)
class GameFinanceAdmin(admin.ModelAdmin):
    """Interface d'administration pour les finances des jeux."""
    
    list_display = (
        'game', 'total_revenue_display', 'platform_fees_display',
        'organizer_profit_display', 'settled', 'settled_at'
    )
    list_filter = ('settled', 'created_at', 'settled_at')
    search_fields = ('game__name',)
    readonly_fields = (
        'platform_fee_percentage', 'profit_margin', 'payout_ratio',
        'created_at', 'updated_at', 'settled_at'
    )
    
    fieldsets = (
        ('Jeu', {
            'fields': ('game',)
        }),
        ('Revenus', {
            'fields': ('total_revenue', 'total_tickets_sold')
        }),
        ('Frais', {
            'fields': ('platform_fees', 'gateway_fees')
        }),
        ('Profits & Paiements', {
            'fields': ('organizer_profit', 'total_prize_payout')
        }),
        ('Règlement', {
            'fields': ('settled', 'settled_at', 'settlement_reference')
        }),
        ('Statistiques', {
            'fields': ('platform_fee_percentage', 'profit_margin', 'payout_ratio'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_settled', 'generate_report']
    
    def total_revenue_display(self, obj):
        """Affichage du revenu total."""
        return format_html('${:,.2f}', obj.total_revenue)
    total_revenue_display.short_description = 'Revenu Total'
    
    def platform_fees_display(self, obj):
        """Affichage des frais de plateforme."""
        return format_html('${:,.2f}', obj.platform_fees)
    platform_fees_display.short_description = 'Frais Plateforme'
    
    def organizer_profit_display(self, obj):
        """Affichage du profit organisateur."""
        return format_html(
            '<span style="color: green; font-weight: bold;">${:,.2f}</span>',
            obj.organizer_profit
        )
    organizer_profit_display.short_description = 'Profit Organisateur'
    
    def platform_fee_percentage(self, obj):
        """Pourcentage de frais plateforme."""
        return obj.platform_fee_percentage()
    platform_fee_percentage.short_description = '% Frais'
    
    def profit_margin(self, obj):
        """Marge de profit."""
        return obj.profit_margin()
    profit_margin.short_description = 'Marge'
    
    def payout_ratio(self, obj):
        """Ratio de paiement."""
        return obj.payout_ratio()
    payout_ratio.short_description = 'Ratio Paiement'
    
    def mark_as_settled(self, request, queryset):
        """Marquer comme réglé."""
        from django.utils import timezone
        count = 0
        for finance in queryset.filter(settled=False):
            finance.settled = True
            finance.settled_at = timezone.now()
            finance.save()
            count += 1
        self.message_user(request, f'{count} finances réglées.')
    mark_as_settled.short_description = 'Marquer comme réglé'
    
    def generate_report(self, request, queryset):
        """Générer un rapport."""
        self.message_user(request, 'Fonctionnalité de rapport à implémenter.')
    generate_report.short_description = 'Générer rapport'


# ============================================================================
# SYNDICATE & SYNDICATEMEMBER ADMIN
# ============================================================================

class SyndicateMemberInline(admin.TabularInline):
    """Inline pour les membres d'un syndicat."""
    model = SyndicateMember
    extra = 0
    readonly_fields = ('joined_at',)
    fields = ('user', 'shares', 'share_of_winnings', 'winnings_paid', 'joined_at')


@admin.register(Syndicate)
class SyndicateAdmin(admin.ModelAdmin):
    """Interface d'administration pour les syndicats."""
    
    list_display = (
        'name', 'game', 'creator', 'total_shares', 'current_members_count',
        'is_active', 'fill_percentage_display', 'created_at'
    )
    list_filter = ('is_active', 'created_at', 'game')
    search_fields = ('name', 'creator__username')
    readonly_fields = (
        'current_members_count', 'available_shares_count',
        'fill_percentage_display', 'created_at', 'updated_at'
    )
    inlines = [SyndicateMemberInline]
    
    fieldsets = (
        ('Informations du Syndicat', {
            'fields': ('name', 'description', 'game', 'creator')
        }),
        ('Parts', {
            'fields': ('total_shares', 'share_price')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Statistiques', {
            'fields': (
                'current_members_count', 'available_shares_count',
                'fill_percentage_display'
            ),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['close_syndicates']
    
    def current_members_count(self, obj):
        """Nombre de membres actuels."""
        return obj.current_members()
    current_members_count.short_description = 'Membres'
    
    def available_shares_count(self, obj):
        """Parts disponibles."""
        return obj.available_shares()
    available_shares_count.short_description = 'Parts Disponibles'
    
    def fill_percentage_display(self, obj):
        """Pourcentage de remplissage."""
        percentage = obj.fill_percentage()
        color = 'green' if percentage >= 75 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.0f}%</span>',
            color, percentage
        )
    fill_percentage_display.short_description = '% Rempli'
    
    def close_syndicates(self, request, queryset):
        """Fermer les syndicats."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} syndicats fermés.')
    close_syndicates.short_description = 'Fermer les syndicats'


@admin.register(SyndicateMember)
class SyndicateMemberAdmin(admin.ModelAdmin):
    """Interface d'administration pour les membres de syndicat."""
    
    list_display = (
        'user', 'syndicate', 'shares', 'share_of_winnings_display',
        'winnings_paid', 'joined_at'
    )
    list_filter = ('winnings_paid', 'joined_at')
    search_fields = ('user__username', 'syndicate__name')
    readonly_fields = ('joined_at',)
    
    def share_of_winnings_display(self, obj):
        """Affichage de la part des gains."""
        if obj.share_of_winnings > 0:
            return format_html(
                '<span style="color: green;">${:,.2f}</span>',
                obj.share_of_winnings
            )
        return '-'
    share_of_winnings_display.short_description = 'Part des Gains'


# ============================================================================
# WALLET ADMIN
# ============================================================================

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Interface d'administration pour les portefeuilles."""
    
    list_display = (
        'user', 'wallet_type_display', 'balance_display', 'is_active'
    )
    list_filter = ('wallet_type', 'is_active')
    search_fields = ('user__username',)
    
    fieldsets = (
        ('Informations du Portefeuille', {
            'fields': ('user', 'wallet_type', 'balance', 'is_active')
        }),
    )
    
    actions = ['activate_wallets', 'deactivate_wallets']
    
    def wallet_type_display(self, obj):
        """Affichage du type de portefeuille."""
        colors = {
            'main': 'blue',
            'bonus': 'orange',
            'winnings': 'green'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.wallet_type, 'black'),
            obj.get_wallet_type_display()
        )
    wallet_type_display.short_description = 'Type'
    
    def balance_display(self, obj):
        """Affichage du solde."""
        color = 'green' if obj.balance > 0 else 'red' if obj.balance < 0 else 'black'
        return format_html(
            '<span style="color: {}; font-weight: bold;">${:,.2f}</span>',
            color, obj.balance
        )
    balance_display.short_description = 'Solde'
    
    def activate_wallets(self, request, queryset):
        """Activer les portefeuilles."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} portefeuilles activés.')
    activate_wallets.short_description = 'Activer'
    
    def deactivate_wallets(self, request, queryset):
        """Désactiver les portefeuilles."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} portefeuilles désactivés.')
    deactivate_wallets.short_description = 'Désactiver'


# ============================================================================
# AUDITLOG ADMIN
# ============================================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Interface d'administration pour les journaux d'audit."""
    
    list_display = (
        'action_display', 'user_link', 'level_display',
        'ip_address', 'created_at'
    )
    list_filter = ('action', 'level', 'created_at')
    search_fields = ('description', 'user__username', 'ip_address')
    readonly_fields = (
        'user', 'action', 'description', 'level', 'ip_address',
        'user_agent', 'game', 'ticket', 'draw', 'payment',
        'metadata', 'created_at'
    )
    
    fieldsets = (
        ('Action', {
            'fields': ('action', 'description', 'level')
        }),
        ('Utilisateur', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Relations', {
            'fields': ('game', 'ticket', 'draw', 'payment'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Date', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        """Empêcher l'ajout manuel."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Empêcher la suppression."""
        return False
    
    def action_display(self, obj):
        """Affichage de l'action."""
        return obj.get_action_display()
    action_display.short_description = 'Action'
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = 'Utilisateur'
    
    def level_display(self, obj):
        """Affichage du niveau."""
        colors = {
            'info': 'blue',
            'warning': 'orange',
            'error': 'red',
            'critical': 'darkred'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.level, 'black'),
            obj.get_level_display().upper()
        )
    level_display.short_description = 'Niveau'
