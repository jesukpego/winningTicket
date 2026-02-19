from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone

from .models import (
    UserProfile,
    Company,
    CompanyUser,
    Game,
    Ticket,
    Winner,
    Draw,
    Payment,
    GameFinance,
    Syndicate,
    SyndicateMember,
    AuditLog,
    Wallet,
)


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class CompanyUserInline(admin.TabularInline):
    model = CompanyUser
    extra = 0
    fields = ('user', 'role', 'is_active', 'can_create_games', 'can_view_finances', 'can_manage_users')
    autocomplete_fields = ['user']


class GameFinanceInline(admin.StackedInline):
    model = GameFinance
    can_delete = False
    extra = 0
    readonly_fields = (
        'total_sales', 'total_tickets', 'platform_fee_amount',
        'organizer_profit', 'total_prize_pool', 'prize_paid_out',
        'prize_remaining', 'last_sale_at', 'prize_settled_at', 'profit_paid_at', 'settled_at',
    )


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    fields = ('ticket_id', 'user', 'status', 'win_amount', 'match_count', 'checked')
    readonly_fields = ('ticket_id',)
    ordering = ('-created_at',)
    show_change_link = True
    max_num = 20


class SyndicateMemberInline(admin.TabularInline):
    model = SyndicateMember
    extra = 0
    fields = ('user', 'shares', 'is_manager', 'paid', 'share_of_winnings', 'winnings_paid')


class WalletInline(admin.TabularInline):
    model = Wallet
    extra = 0
    fields = ('wallet_type', 'balance', 'is_active')


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_spent', 'total_won', 'games_played', 'age_verified', 'created_at')
    list_filter = ('age_verified', 'email_notifications', 'sms_notifications')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'net_profit', 'win_ratio', 'balance')
    fieldsets = (
        ('User Account', {
            'fields': ('user',),
        }),
        ('Financial', {
            'fields': ('total_spent', 'total_won', 'games_played', 'net_profit', 'balance'),
        }),
        ('Compliance', {
            'fields': ('age_verified', 'verification_date'),
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'sms_notifications'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    ordering = ('-created_at',)

    def net_profit(self, obj):
        return obj.net_profit
    net_profit.short_description = 'Net Profit'

    def win_ratio(self, obj):
        return f"{obj.win_ratio:.1f}%"
    win_ratio.short_description = 'Win Ratio'

    def balance(self, obj):
        return obj.balance
    balance.short_description = 'Main Wallet Balance'


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'registration_number', 'contact_email', 'verified', 'is_active', 'balance', 'total_games', 'active_games', 'created_at')
    list_filter = ('verified', 'is_active')
    search_fields = ('name', 'registration_number', 'contact_email')
    readonly_fields = ('created_at', 'updated_at', 'verified_at', 'total_games', 'active_games')
    inlines = [CompanyUserInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'registration_number'),
        }),
        ('Contact', {
            'fields': ('contact_email', 'contact_phone', 'address'),
        }),
        ('Status', {
            'fields': ('verified', 'is_active', 'balance'),
        }),
        ('Statistics', {
            'fields': ('total_games', 'active_games'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'verified_at'),
            'classes': ('collapse',),
        }),
    )
    ordering = ('name',)

    def total_games(self, obj):
        return obj.total_games
    total_games.short_description = 'Total Games'

    def active_games(self, obj):
        return obj.active_games
    active_games.short_description = 'Active Games'


# ---------------------------------------------------------------------------
# CompanyUser
# ---------------------------------------------------------------------------

@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role', 'is_active', 'can_create_games', 'can_view_finances', 'can_manage_users', 'created_at')
    list_filter = ('role', 'is_active', 'can_create_games', 'can_view_finances', 'can_manage_users')
    search_fields = ('user__username', 'company__name')
    autocomplete_fields = ['user', 'company']
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('company', 'role')


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'company', 'status', 'ticket_price', 'prize_amount',
        'total_tickets_sold', 'progression_percentage', 'next_draw', 'created_at',
    )
    list_filter = ('status', 'company')
    search_fields = ('name', 'slug', 'company__name')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = (
        'created_at', 'updated_at', 'published_at',
        'total_sales', 'platform_fee_amount', 'organizer_profit',
        'progression_percentage', 'ready_for_draw', 'winners_list',
    )
    inlines = [GameFinanceInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'company'),
        }),
        ('Pricing & Prize', {
            'fields': ('ticket_price', 'prize_amount', 'platform_fee_percent'),
        }),
        ('Game Rules', {
            'fields': ('number_range',),
        }),
        ('Timing', {
            'fields': ('next_draw',),
        }),
        ('Status', {
            'fields': ('status', 'total_tickets_sold'),
        }),
        ('Computed Stats', {
            'fields': ('total_sales', 'platform_fee_amount', 'organizer_profit', 'progression_percentage', 'ready_for_draw'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',),
        }),
    )
    ordering = ('-created_at',)

    def progression_percentage(self, obj):
        pct = obj.progression_percentage
        color = 'green' if pct >= 75 else 'orange' if pct >= 40 else 'red'
        return format_html('<span style="color:{}">{:.1f}%</span>', color, pct)
    progression_percentage.short_description = 'Progress'

    def ready_for_draw(self, obj):
        return obj.ready_for_draw
    ready_for_draw.boolean = True
    ready_for_draw.short_description = 'Ready for Draw'

    def total_sales(self, obj):
        return f"${obj.total_sales:,.2f}"
    total_sales.short_description = 'Total Sales'

    def platform_fee_amount(self, obj):
        return f"${obj.platform_fee_amount:,.2f}"
    platform_fee_amount.short_description = 'Platform Fee'

    def organizer_profit(self, obj):
        return f"${obj.organizer_profit:,.2f}"
    organizer_profit.short_description = 'Organizer Profit'

    def winners_list(self, obj):
        return ', '.join(str(w) for w in obj.winners_list)
    winners_list.short_description = 'Winners'


# ---------------------------------------------------------------------------
# Ticket
# ---------------------------------------------------------------------------

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user', 'game', 'status', 'win_amount', 'match_count', 'checked', 'draw_date', 'created_at')
    list_filter = ('status', 'checked', 'game')
    search_fields = ('ticket_id', 'user__username', 'game__name')
    readonly_fields = ('ticket_id', 'created_at', 'checked_at', 'is_winner')
    autocomplete_fields = ['user', 'game', 'draw']
    fieldsets = (
        ('Identification', {
            'fields': ('ticket_id',),
        }),
        ('Ownership', {
            'fields': ('user', 'game', 'draw'),
        }),
        ('Numbers & Draw', {
            'fields': ('numbers', 'draw_date'),
        }),
        ('Status & Results', {
            'fields': ('status', 'win_amount', 'match_count', 'checked', 'is_winner'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'checked_at'),
            'classes': ('collapse',),
        }),
    )
    ordering = ('-created_at',)

    def is_winner(self, obj):
        return obj.is_winner
    is_winner.boolean = True
    is_winner.short_description = 'Winner?'


# ---------------------------------------------------------------------------
# Draw
# ---------------------------------------------------------------------------

@admin.register(Draw)
class DrawAdmin(admin.ModelAdmin):
    list_display = (
        'draw_number', 'game', 'draw_date', 'jackpot_amount', 'jackpot_won',
        'total_tickets', 'total_winners', 'total_prize_paid', 'processed',
    )
    list_filter = ('processed', 'jackpot_won', 'game')
    search_fields = ('game__name', 'draw_number')
    readonly_fields = ('created_at', 'updated_at', 'processed_at', 'winning_numbers_display', 'prize_pool_breakdown')
    inlines = [TicketInline]
    fieldsets = (
        ('Draw Info', {
            'fields': ('game', 'draw_number', 'draw_date', 'winning_numbers', 'winning_numbers_display'),
        }),
        ('Jackpot', {
            'fields': ('jackpot_amount', 'jackpot_won'),
        }),
        ('Statistics', {
            'fields': ('total_tickets', 'total_winners', 'total_prize_paid', 'prize_pool_breakdown'),
        }),
        ('Processing', {
            'fields': ('processed', 'processed_at', 'created_by', 'verified_by'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    autocomplete_fields = ['game']
    ordering = ('-draw_date',)

    def winning_numbers_display(self, obj):
        return obj.winning_numbers_display
    winning_numbers_display.short_description = 'Winning Numbers (Sorted)'

    def prize_pool_breakdown(self, obj):
        bd = obj.prize_pool_breakdown
        return f"Jackpot: ${bd['jackpot']:,.2f} | Other: ${bd['other_prizes']:,.2f} | Total: ${bd['total']:,.2f}"
    prize_pool_breakdown.short_description = 'Prize Pool Breakdown'


# ---------------------------------------------------------------------------
# Winner
# ---------------------------------------------------------------------------

@admin.register(Winner)
class WinnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'draw', 'prize_amount', 'tax_withheld', 'net_amount', 'claimed', 'claimed_at', 'paid', 'paid_at')
    list_filter = ('claimed', 'paid', 'payout_method')
    search_fields = ('user__username', 'ticket__ticket_id', 'payout_reference')
    readonly_fields = ('created_at', 'updated_at', 'net_amount', 'days_since_win', 'tax_percentage_calculated')
    autocomplete_fields = ['user', 'ticket', 'draw']
    fieldsets = (
        ('Winner Info', {
            'fields': ('user', 'ticket', 'draw'),
        }),
        ('Prize', {
            'fields': ('prize_amount', 'tax_withheld', 'tax_percentage', 'net_amount', 'tax_percentage_calculated'),
        }),
        ('Claim', {
            'fields': ('claimed', 'claimed_at'),
        }),
        ('Payment', {
            'fields': ('paid', 'paid_at', 'payout_method', 'payout_reference'),
        }),
        ('Info', {
            'fields': ('days_since_win', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    ordering = ('-prize_amount',)

    def net_amount(self, obj):
        return f"${obj.net_amount:,.2f}"
    net_amount.short_description = 'Net Amount'

    def days_since_win(self, obj):
        return obj.days_since_win
    days_since_win.short_description = 'Days Since Win'

    def tax_percentage_calculated(self, obj):
        return f"{obj.tax_percentage_calculated:.2f}%"
    tax_percentage_calculated.short_description = 'Effective Tax %'


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'user', 'payment_type', 'payment_method',
        'amount', 'processing_fee', 'net_amount', 'status', 'created_at',
    )
    list_filter = ('status', 'payment_type', 'payment_method')
    search_fields = ('transaction_id', 'internal_reference', 'user__username', 'gateway_transaction_id')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'is_successful', 'formatted_amount', 'age_in_minutes')
    autocomplete_fields = ['user', 'game', 'ticket']
    fieldsets = (
        ('Transaction IDs', {
            'fields': ('transaction_id', 'internal_reference', 'gateway_transaction_id'),
        }),
        ('Parties', {
            'fields': ('user', 'game', 'ticket'),
        }),
        ('Payment Details', {
            'fields': ('amount', 'processing_fee', 'net_amount', 'payment_type', 'payment_method', 'status'),
        }),
        ('Gateway', {
            'fields': ('gateway_response',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'is_successful', 'formatted_amount', 'age_in_minutes'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )
    ordering = ('-created_at',)

    def is_successful(self, obj):
        return obj.is_successful
    is_successful.boolean = True
    is_successful.short_description = 'Successful?'

    def formatted_amount(self, obj):
        return obj.formatted_amount
    formatted_amount.short_description = 'Formatted Amount'

    def age_in_minutes(self, obj):
        return f"{obj.age_in_minutes:.1f} min"
    age_in_minutes.short_description = 'Age (minutes)'


# ---------------------------------------------------------------------------
# GameFinance
# ---------------------------------------------------------------------------

@admin.register(GameFinance)
class GameFinanceAdmin(admin.ModelAdmin):
    list_display = (
        'game', 'total_sales', 'total_tickets', 'platform_fee_amount',
        'organizer_profit', 'total_prize_pool', 'prize_paid_out',
        'settled', 'prize_paid', 'fees_settled', 'profit_paid',
    )
    list_filter = ('settled', 'prize_paid', 'fees_settled', 'profit_paid')
    search_fields = ('game__name',)
    autocomplete_fields = ['game']
    readonly_fields = (
        'created_at', 'updated_at',
        'platform_fee_percentage', 'profit_margin', 'payout_ratio',
        'last_sale_at', 'prize_settled_at', 'profit_paid_at', 'settled_at',
    )
    fieldsets = (
        ('Game', {
            'fields': ('game',),
        }),
        ('Sales', {
            'fields': ('total_sales', 'total_tickets', 'last_sale_at'),
        }),
        ('Revenue Distribution', {
            'fields': ('platform_fee_amount', 'organizer_profit'),
        }),
        ('Prize', {
            'fields': ('total_prize_pool', 'prize_paid_out', 'prize_remaining'),
        }),
        ('Settlement', {
            'fields': ('prize_paid', 'fees_settled', 'profit_paid', 'settled', 'prize_settled_at', 'profit_paid_at', 'settled_at'),
        }),
        ('Analytics', {
            'fields': ('platform_fee_percentage', 'profit_margin', 'payout_ratio'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    ordering = ('-created_at',)

    def platform_fee_percentage(self, obj):
        return f"{obj.platform_fee_percentage:.2f}%"
    platform_fee_percentage.short_description = 'Platform Fee %'

    def profit_margin(self, obj):
        return f"{obj.profit_margin:.2f}%"
    profit_margin.short_description = 'Profit Margin'

    def payout_ratio(self, obj):
        return f"{obj.payout_ratio:.2f}%"
    payout_ratio.short_description = 'Payout Ratio'


# ---------------------------------------------------------------------------
# Syndicate
# ---------------------------------------------------------------------------

@admin.register(Syndicate)
class SyndicateAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'creator', 'max_members', 'current_members', 'total_shares', 'available_shares', 'is_active', 'is_full', 'created_at')
    list_filter = ('is_active', 'is_full', 'game')
    search_fields = ('name', 'creator__username', 'game__name')
    readonly_fields = ('created_at', 'updated_at', 'current_members', 'available_shares', 'fill_percentage')
    inlines = [SyndicateMemberInline]
    autocomplete_fields = ['creator', 'game']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'creator', 'game'),
        }),
        ('Structure', {
            'fields': ('max_members', 'ticket_price', 'share_price', 'total_shares', 'numbers'),
        }),
        ('Status', {
            'fields': ('is_active', 'is_full'),
        }),
        ('Statistics', {
            'fields': ('current_members', 'available_shares', 'fill_percentage'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    ordering = ('-created_at',)

    def current_members(self, obj):
        return obj.current_members
    current_members.short_description = 'Members'

    def available_shares(self, obj):
        return obj.available_shares
    available_shares.short_description = 'Available Shares'

    def fill_percentage(self, obj):
        return f"{obj.fill_percentage:.1f}%"
    fill_percentage.short_description = 'Fill %'


# ---------------------------------------------------------------------------
# SyndicateMember
# ---------------------------------------------------------------------------

@admin.register(SyndicateMember)
class SyndicateMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'syndicate', 'shares', 'is_manager', 'paid', 'share_of_winnings', 'winnings_paid', 'joined_at')
    list_filter = ('is_manager', 'paid', 'winnings_paid')
    search_fields = ('user__username', 'syndicate__name')
    autocomplete_fields = ['user', 'syndicate', 'payment']
    readonly_fields = ('joined_at',)
    ordering = ('-joined_at',)


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'level', 'user', 'ip_address', 'created_at')
    list_filter = ('action', 'level')
    search_fields = ('user__username', 'description', 'ip_address')
    readonly_fields = (
        'action', 'level', 'description', 'user', 'ip_address', 'user_agent',
        'game', 'ticket', 'draw', 'payment', 'metadata', 'created_at',
    )
    fieldsets = (
        ('Event', {
            'fields': ('action', 'level', 'description'),
        }),
        ('Actor', {
            'fields': ('user', 'ip_address', 'user_agent'),
        }),
        ('Related Objects', {
            'fields': ('game', 'ticket', 'draw', 'payment'),
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',),
        }),
        ('Timestamp', {
            'fields': ('created_at',),
        }),
    )
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False  # Audit logs should only be created programmatically

    def has_change_permission(self, request, obj=None):
        return False  # Audit logs are immutable


# ---------------------------------------------------------------------------
# Wallet
# ---------------------------------------------------------------------------

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet_type', 'balance', 'is_active')
    list_filter = ('wallet_type', 'is_active')
    search_fields = ('user__username',)
    autocomplete_fields = ['user']
    ordering = ('user', 'wallet_type')
