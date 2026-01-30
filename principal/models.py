
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

class UserProfile(models.Model):
    """
    Extended user profile for lottery players.
    
    Stores additional information beyond Django's built-in User model.
    Includes responsible gaming features and player statistics.
    """
    
    # One-to-one link with Django's User model
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Django User Account"
    )
    
    # Financial tracking
    total_spent = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Total Amount Spent on Tickets"
    )
    total_won = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Total Winnings Received"
    )
    
    # Activity tracking
    games_played = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Tickets Purchased"
    )
    

    # Compliance fields
    age_verified = models.BooleanField(
        default=False,
        verbose_name="Age Verification Completed"
    )
    verification_date = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Date of Age Verification"
    )
    
    # Preferences
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Receive Email Notifications"
    )
    sms_notifications = models.BooleanField(
        default=False,
        verbose_name="Receive SMS Notifications"
    )
    
   


    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Profile: {self.user.username}"
    
    def can_make_purchase(self, amount):
        """
        Check if user can make a purchase based on spending limits.
        
        Args:
            amount (Decimal): Purchase amount to check
            
        Returns:
            tuple: (can_purchase: bool, reason: str)
        """
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        
        # Check daily limit
        daily_spent = self.user.payments.filter(
            created_at__date=today,
            payment_type='ticket',
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        if daily_spent + amount > self.daily_limit:
            return False, f"Daily limit of ${self.daily_limit} exceeded"
        
        # Check weekly limit if set
        if self.weekly_limit > 0:
            week_ago = today - timedelta(days=7)
            weekly_spent = self.user.payments.filter(
                created_at__date__gte=week_ago,
                payment_type='ticket',
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            if weekly_spent + amount > self.weekly_limit:
                return False, f"Weekly limit of ${self.weekly_limit} exceeded"
        
        return True, "OK"
    
    @property
    def net_profit(self):
        """Calculate user's net profit/loss"""
        return self.total_won - self.total_spent
    
    @property
    def win_ratio(self):
        """Calculate win ratio (games won / games played)"""
        if self.games_played == 0:
            return 0
        return (self.user.tickets.filter(status='won').count() / self.games_played) * 100



class Company(models.Model):
    """
    Registered company that can organize lottery games.
    
    Companies go through a verification process before they can
    create games. Each company can have multiple users with different roles.
    """
    
    # Basic information
    name = models.CharField(
        max_length=150,
        verbose_name="Company Legal Name"
    )
    registration_number = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Business Registration Number"
    )
    
    # Contact information
    contact_email = models.EmailField(
        verbose_name="Primary Contact Email"
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Contact Phone Number"
    )
    address = models.TextField(
        blank=True,
        verbose_name="Registered Address"
    )
    
    # Status
    verified = models.BooleanField(
        default=False,
        verbose_name="Company Verified by Platform"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Account Active"
    )
    
    # Financial
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Available Balance"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ['name']
        indexes = [
            models.Index(fields=['verified', 'is_active']),
            models.Index(fields=['registration_number']),
        ]
    
    def __str__(self):
        return f"{self.name} ({'✓' if self.verified else '✗'})"
    
    def clean(self):
        """Validate company data"""
        if self.verified and not self.verified_at:
            self.verified_at = timezone.now()
        
        if not self.registration_number:
            raise ValidationError("Registration number is required")
    
    @property
    def total_games(self):
        """Total games created by this company"""
        return self.games.count()
    
    @property
    def active_games(self):
        """Currently active games"""
        return self.games.filter(status='active').count()


class CompanyUser(models.Model):
    """
    Link between User and Company with specific role.
    
    A user can be part of multiple companies with different roles.
    This enables the company dashboard access.
    """
    
    ROLE_CHOICES = [
        ('admin', 'Administrator - Full Access'),
        ('manager', 'Manager - Operational Access'),
        ('finance', 'Finance - Financial Access'),
        ('viewer', 'Viewer - Read Only'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='company_roles',
        verbose_name="User Account"
    )
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        related_name='company_users',
        verbose_name="Company"
    )
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES,
        default='viewer',
        verbose_name="User Role in Company"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Role Active"
    )
    
    # Permissions (could also use Django permissions system)
    can_create_games = models.BooleanField(
        default=False,
        verbose_name="Can Create Games"
    )
    can_view_finances = models.BooleanField(
        default=False,
        verbose_name="Can View Financial Data"
    )
    can_manage_users = models.BooleanField(
        default=False,
        verbose_name="Can Manage Company Users"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Company User"
        verbose_name_plural = "Company Users"
        unique_together = ('user', 'company')
        ordering = ['company', 'role']
    
    def __str__(self):
        return f"{self.user.username} → {self.company.name} ({self.role})"
    
    def save(self, *args, **kwargs):
        """Auto-set permissions based on role"""
        if self.role == 'admin':
            self.can_create_games = True
            self.can_view_finances = True
            self.can_manage_users = True
        elif self.role == 'manager':
            self.can_create_games = True
            self.can_view_finances = True
            self.can_manage_users = False
        elif self.role == 'finance':
            self.can_create_games = False
            self.can_view_finances = True
            self.can_manage_users = False
        
        super().save(*args, **kwargs)



class Game(models.Model):
    """
    Lottery game definition.
    
    Can be created by platform, individual organizer, or company.
    Defines all rules, pricing, and timing for a lottery game.
    """
    
    
    
    STATUS = [
        ('draft', 'Draft - Not Published'),
        ('pending', 'Pending Approval'),
        ('active', 'Active - Accepting Tickets'),
        ('closed', 'Closed - Draw Completed'),
        ('canceled', 'Canceled - No Draw'),
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=100,
        verbose_name="Game Name",
        help_text="Public name of the lottery game"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="URL Slug",
        help_text="URL-friendly version of name"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Game Description",
        help_text="Detailed description for players"
    )
    
    # Company is the organizer
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='games',
        verbose_name="Company Organizer"
    )
    
    # Pricing
    ticket_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Price per Ticket",
        help_text="Amount user pays for one ticket"
    )
    prize_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Total Prize Amount",
        help_text="Amount to be distributed to winners"
    )
    
    # Commission Structure
    platform_fee_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=10.00,
        verbose_name="Platform Commission (%)",
        help_text="Percentage taken by platform from ticket sales"
    )
    
    # Game Rules
  
    number_range = models.PositiveIntegerField(
        default=50,
        verbose_name="Number Range (1 to X)"
    )
    
    
    
    # Status
    status = models.CharField(
        max_length=10, 
        choices=STATUS, 
        default='draft',
        verbose_name="Game Status"
    )
    
    # Statistics
    total_tickets_sold = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Tickets Sold"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Game"
        verbose_name_plural = "Games"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['slug']),
            models.Index(fields=['company']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def clean(self):
        """Validate game data"""
        errors = {}
        
        # Validate company is provided (use company_id to avoid RelatedObjectDoesNotExist)
        if not self.company_id:
            errors['company'] = "L'entreprise est requise pour tous les jeux"
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Auto-set published_at when status becomes active and create GameFinance"""
        is_new = self.pk is None
        
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
            
        if self.status == 'active' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Auto-create GameFinance for new games
        if is_new:
            from principal.models import GameFinance
            GameFinance.objects.get_or_create(
                game=self,
                defaults={
                    'total_prize_pool': self.prize_amount,
                }
            )
    
    @property
    def total_sales(self):
        """Calculate total sales amount"""
        return self.ticket_price * self.total_tickets_sold
    
    @property
    def platform_fee_amount(self):
        """Calculate platform fee in dollars"""
        return (self.total_sales * self.platform_fee_percent) / 100
    
    @property
    def organizer_profit(self):
        """Calculate organizer's profit"""
        return self.total_sales - self.platform_fee_amount - self.prize_amount
    
    @property
    def is_open_for_sales(self):
        """Check if tickets can be sold now"""
        if self.status != 'active':
            return False
        
        now = timezone.now()
        if self.ticket_sale_end and now > self.ticket_sale_end:
            return False
        
        return True
    
    def get_odds(self, match_count, has_powerball=False):
        """
        Calculate odds of winning based on match count.
        
        Note: This is a simplified calculation. Real lottery odds
        would require combinatorial mathematics.
        """
        # Simplified odds calculation
        import math
        
        n = self.number_range
        k = self.max_numbers
        
        # Combinations formula: C(n, k) = n! / (k! * (n-k)!)
        total_combinations = math.comb(n, k)
        
        if self.has_powerball and has_powerball:
            total_combinations *= self.powerball_range
        
        # For simplicity, return approximate odds
        if match_count == k:
            return f"1 in {total_combinations:,}"
        else:
            return "Varies based on exact match"
    
    def can_user_buy_ticket(self, user):
        """Check if user can buy a ticket for this game"""
        if not self.is_open_for_sales:
            return False, "Game not open for ticket sales"
        
        if not hasattr(user, 'profile'):
            return False, "User profile not found"
        
        # Check spending limits
        can_purchase, reason = user.profile.can_make_purchase(self.ticket_price)
        if not can_purchase:
            return False, reason
        
        return True, "OK"


class Ticket(models.Model):
    """
    Individual lottery ticket purchase.
    
    Each ticket represents a player's participation in a specific draw
    of a specific game with chosen numbers.
    """
    
    STATUS = [
        ('pending', 'Pending - Awaiting Draw'),
        ('won', 'Won - Winning Ticket'),
        ('lost', 'Lost - Non-winning Ticket'),
        ('refunded', 'Refunded - Purchase Refunded'),
    ]
    
    # Identification
    ticket_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Public Ticket ID",
        help_text="Format: GAME-YYYYMMDD-XXXXX"
    )
    
    # Ownership
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name="Ticket Owner"
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name="Game"
    )
    
    # Game References
    draw = models.ForeignKey(
        'Draw',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name="Associated Draw",
        help_text="Draw this ticket participates in"
    )
    
    # Numbers Selected
    numbers = models.JSONField(
        verbose_name="Selected Numbers",
        help_text="Array of selected numbers, e.g., [1, 15, 23, 34, 45]"
    )
    powerball = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Powerball Number",
        help_text="Only if game has_powerball is True"
    )
    
    # Draw Information
    draw_date = models.DateTimeField(
        verbose_name="Scheduled Draw Date"
    )
    
    # Status & Results
    status = models.CharField(
        max_length=10, 
        choices=STATUS, 
        default='pending',
        verbose_name="Ticket Status"
    )
    win_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Amount Won"
    )
    
    # Verification
    checked = models.BooleanField(
        default=False,
        verbose_name="Checked Against Draw"
    )
    
    # Winning Details
    match_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Numbers Matched"
    )
    has_powerball_match = models.BooleanField(
        default=False,
        verbose_name="Powerball Matched"
    )
    prize_tier = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Prize Tier",
        help_text="e.g., 'Match 5 + Powerball'"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['game', 'draw_date']),
            models.Index(fields=['ticket_id']),
            models.Index(fields=['status', 'checked']),
        ]
    
    def __str__(self):
        return f"Ticket {self.ticket_id} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        """Generate ticket ID on creation"""
        if not self.ticket_id:
            # Format: GAME-ID-YYYYMMDD-RANDOM
            import random
            import string
            from django.utils import timezone
            
            game_prefix = self.game.slug.upper()[:4]
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = ''.join(random.choices(string.digits, k=5))
            self.ticket_id = f"{game_prefix}-{date_str}-{random_str}"
        
        # Set draw_date from game if not set, default to now if game has no next_draw logic
        if not self.draw_date:
            if self.game and hasattr(self.game, 'next_draw'):
                self.draw_date = self.game.next_draw
            else:
                from django.utils import timezone
                self.draw_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def check_win(self, draw=None):
        """
        Check if this ticket is a winning ticket.
        
        Args:
            draw (Draw, optional): Draw to check against. Uses self.draw if not provided.
            
        Returns:
            dict: Results including match_count, has_powerball_match, win_amount
        """
        if not draw:
            draw = self.draw
        
        if not draw:
            return {
                'is_winner': False,
                'error': 'No draw associated with ticket'
            }
        
        # Get numbers
        ticket_numbers = set(self.numbers)
        winning_numbers = set(draw.winning_numbers)
        
        # Calculate matches
        self.match_count = len(ticket_numbers.intersection(winning_numbers))
        self.has_powerball_match = (
            self.game.has_powerball and 
            self.powerball == draw.winning_powerball
        )
        
        # Determine prize tier (simplified - implement based on your prize structure)
        self.prize_tier = self._determine_prize_tier()
        
        # Check if winner
        is_winner = self._is_winning_ticket()
        
        if is_winner:
            self.status = 'won'
            # Calculate win amount (implement based on your prize structure)
            self.win_amount = self._calculate_win_amount()
        else:
            self.status = 'lost'
            self.win_amount = 0
        
        self.checked = True
        self.checked_at = timezone.now()
        self.save()
        
        return {
            'is_winner': is_winner,
            'match_count': self.match_count,
            'has_powerball_match': self.has_powerball_match,
            'prize_tier': self.prize_tier,
            'win_amount': self.win_amount,
            'ticket_id': self.ticket_id
        }
    
    def _determine_prize_tier(self):
        """Determine prize tier based on matches"""
        if not self.game.has_powerball:
            if self.match_count == self.game.max_numbers:
                return f"Match {self.match_count}"
            elif self.match_count >= self.game.min_numbers:
                return f"Match {self.match_count}"
            else:
                return ""
        else:
            if self.match_count == self.game.max_numbers and self.has_powerball_match:
                return f"Match {self.match_count} + Powerball"
            elif self.match_count == self.game.max_numbers:
                return f"Match {self.match_count}"
            elif self.match_count >= self.game.min_numbers:
                return f"Match {self.match_count}" + (" + Powerball" if self.has_powerball_match else "")
            else:
                return ""
    
    def _is_winning_ticket(self):
        """Check if this is a winning ticket"""
        # At least match minimum numbers
        if self.match_count < self.game.min_numbers:
            return False
        
        # If game has powerball, check powerball rules
        if self.game.has_powerball:
            # You might want to adjust these rules
            return self.match_count >= self.game.min_numbers or self.has_powerball_match
        
        return self.match_count >= self.game.min_numbers
    
    def _calculate_win_amount(self):
        """Calculate win amount based on prize tier"""
        # Implement your prize distribution logic here
        # This is a simplified example
        
        prize_structure = {
            f"Match {self.game.max_numbers} + Powerball": self.game.prize_amount * 0.5,
            f"Match {self.game.max_numbers}": self.game.prize_amount * 0.2,
            f"Match {self.game.max_numbers - 1} + Powerball": self.game.prize_amount * 0.1,
            # Add more tiers as needed
        }
        
        return prize_structure.get(self.prize_tier, 0)
    
    @property
    def is_winner(self):
        """Check if ticket is a winner"""
        return self.status == 'won' and self.win_amount > 0
    
    @property
    def numbers_display(self):
        """Display numbers in human-readable format"""
        nums = ', '.join(str(n) for n in sorted(self.numbers))
        if self.powerball:
            nums += f" + {self.powerball}"
        return nums


class Draw(models.Model):
    """
    Lottery draw event with winning numbers.
    
    Each draw is associated with a specific game and contains
    the official winning numbers for that draw.
    """
    
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='draws',
        verbose_name="Game"
    )
    
    # Draw Information
    draw_date = models.DateTimeField(
        verbose_name="Actual Draw Date & Time"
    )
    draw_number = models.PositiveIntegerField(
        verbose_name="Draw Sequence Number",
        help_text="e.g., 1234 (incremental per game)"
    )
    
    # Winning Numbers
    winning_numbers = models.JSONField(
        verbose_name="Winning Numbers",
        help_text="Array of winning numbers"
    )
    winning_powerball = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Winning Powerball",
        help_text="Only if game has_powerball is True"
    )
    
    # Jackpot Information
    jackpot_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name="Jackpot Amount for This Draw"
    )
    jackpot_won = models.BooleanField(
        default=False,
        verbose_name="Jackpot Won in This Draw"
    )
    
    # Statistics
    total_tickets = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Tickets for This Draw"
    )
    total_winners = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Winning Tickets"
    )
    total_prize_paid = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name="Total Prize Money Paid"
    )
    
    # Processing Status
    processed = models.BooleanField(
        default=False,
        verbose_name="Draw Processed"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Processing Completion Time"
    )
    
    # Audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Draw Created By"
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_draws',
        verbose_name="Draw Verified By"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Draw"
        verbose_name_plural = "Draws"
        unique_together = ('game', 'draw_number')
        ordering = ['-draw_date']
        indexes = [
            models.Index(fields=['game', 'draw_date']),
            models.Index(fields=['processed']),
            models.Index(fields=['draw_number']),
        ]
    
    def __str__(self):
        return f"Draw #{self.draw_number} - {self.game.name} - {self.draw_date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        """Auto-increment draw number"""
        if not self.draw_number:
            last_draw = Draw.objects.filter(game=self.game).order_by('-draw_number').first()
            self.draw_number = last_draw.draw_number + 1 if last_draw else 1
        super().save(*args, **kwargs)
    
    def process_draw(self):
        """
        Process the draw: check all tickets and identify winners.
        
        This should be run as a background task (Celery) for large draws.
        """
        from django.db import transaction
        
        if self.processed:
            return {"status": "already_processed", "message": "Draw already processed"}
        
        with transaction.atomic():
            # Get all tickets for this draw
            tickets = self.tickets.filter(status='pending')
            
            winners = []
            total_prize = 0
            
            for ticket in tickets:
                result = ticket.check_win(self)
                
                if result['is_winner']:
                    # Create Winner record
                    winner = Winner.objects.create(
                        user=ticket.user,
                        ticket=ticket,
                        draw=self,
                        prize_amount=result['win_amount'],
                        prize_tier=result['prize_tier']
                    )
                    winners.append(winner)
                    total_prize += result['win_amount']
            
            # Update draw statistics
            self.total_winners = len(winners)
            self.total_prize_paid = total_prize
            self.processed = True
            self.processed_at = timezone.now()
            self.save()
            
            # Update game status if needed
            if self.game.next_draw == self.draw_date:
                self.game.status = 'closed'
                self.game.save()
            
            return {
                "status": "success",
                "total_tickets": tickets.count(),
                "winners": len(winners),
                "total_prize": total_prize,
                "winners_list": [w.id for w in winners]
            }
    
    @property
    def is_jackpot_winner(self):
        """Check if there's a jackpot winner"""
        return self.jackpot_won
    
    @property
    def winning_numbers_display(self):
        """Display winning numbers in human-readable format"""
        nums = ', '.join(str(n) for n in sorted(self.winning_numbers))
        if self.winning_powerball:
            nums += f" + {self.winning_powerball}"
        return nums
    
    @property
    def prize_pool_breakdown(self):
        """Calculate prize pool distribution"""
        # Implement based on your prize structure
        breakdown = {
            'jackpot': self.jackpot_amount,
            'other_prizes': self.game.prize_amount - self.jackpot_amount,
            'total': self.game.prize_amount
        }
        return breakdown


class Winner(models.Model):
    """
    Record of a winning ticket and its prize.
    
    Created when a ticket matches winning numbers.
    Tracks prize payment status and tax information.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='winnings',
        verbose_name="Winner"
    )
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name='winner_record',
        verbose_name="Winning Ticket"
    )
    draw = models.ForeignKey(
        Draw,
        on_delete=models.CASCADE,
        related_name='winners',
        verbose_name="Draw"
    )
    
    # Prize Information
    prize_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Prize Amount"
    )
    prize_tier = models.CharField(
        max_length=100,
        verbose_name="Prize Tier",
        help_text="e.g., 'Match 5 + Powerball'"
    )
    
    # Payment Status
    claimed = models.BooleanField(
        default=False,
        verbose_name="Prize Claimed by Winner"
    )
    claimed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Claim Date"
    )
    
    paid = models.BooleanField(
        default=False,
        verbose_name="Prize Paid to Winner"
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Payment Date"
    )
    
    # Tax Information
    tax_withheld = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Tax Withheld at Source"
    )
    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Tax Percentage Applied"
    )
    
    # Payout Information
    payout_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Payout Method",
        help_text="e.g., 'bank_transfer', 'wallet', 'check'"
    )
    payout_reference = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Payout Reference/Transaction ID"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Winner"
        verbose_name_plural = "Winners"
        ordering = ['-prize_amount']
        indexes = [
            models.Index(fields=['user', 'claimed']),
            models.Index(fields=['paid', 'claimed']),
            models.Index(fields=['draw']),
        ]
    
    def __str__(self):
        return f"Winner: {self.user.username} - ${self.prize_amount} - {self.prize_tier}"
    
    def claim_prize(self):
        """Mark prize as claimed by winner"""
        if not self.claimed:
            self.claimed = True
            self.claimed_at = timezone.now()
            self.save()
            
            # Update user profile
            self.user.profile.total_won += self.prize_amount
            self.user.profile.save()
            
            return True
        return False
    
    def process_payment(self, payout_method='wallet', reference=''):
        """
        Process payment to winner.
        
        Args:
            payout_method (str): Method of payment
            reference (str): Transaction reference
            
        Returns:
            bool: Success status
        """
        if not self.claimed:
            return False
        
        if not self.paid:
            # Calculate net amount after tax
            net_amount = self.prize_amount - self.tax_withheld
            
            # Create payment record
            payment = Payment.objects.create(
                user=self.user,
                amount=net_amount,
                payment_type='payout',
                status='completed',
                transaction_id=f"PAYOUT-{self.id}-{reference}"
            )
            
            # Update winner record
            self.paid = True
            self.paid_at = timezone.now()
            self.payout_method = payout_method
            self.payout_reference = reference
            self.save()
            
            return True
        return False
    
    @property
    def net_amount(self):
        """Calculate net amount after tax"""
        return self.prize_amount - self.tax_withheld
    
    @property
    def tax_percentage_calculated(self):
        """Calculate tax percentage"""
        if self.prize_amount == 0:
            return 0
        return (self.tax_withheld / self.prize_amount) * 100
    
    @property
    def days_since_win(self):
        """Calculate days since winning"""
        from django.utils import timezone
        if not self.created_at:
            return 0
        delta = timezone.now() - self.created_at
        return delta.days


class Payment(models.Model):
    """
    All financial transactions in the system.
    
    Tracks money movements: ticket purchases, prize payouts,
    refunds, and platform commissions.
    """
    
    PAYMENT_TYPE = [
        ('ticket', 'Ticket Purchase'),
        ('payout', 'Prize Payout'),
        ('refund', 'Refund'),
        ('commission', 'Platform Commission'),
        ('deposit', 'Wallet Deposit'),
        ('withdrawal', 'Wallet Withdrawal'),
    ]
    
    STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('ewallet', 'E-Wallet'),
        ('wallet', 'Platform Wallet'),
        ('crypto', 'Cryptocurrency'),
    ]
    
    # Transaction Identification
    transaction_id = models.CharField(
        max_length=150, 
        unique=True,
        verbose_name="Transaction ID",
        help_text="Unique identifier from payment gateway"
    )
    internal_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Internal Reference",
        help_text="Our internal reference (e.g., TICKET-123)"
    )
    
    # User and Context
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="User"
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name="Game (if applicable)"
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name="Ticket (if applicable)"
    )
    
    # Payment Details
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Transaction Amount"
    )
    payment_type = models.CharField(
        max_length=15, 
        choices=PAYMENT_TYPE,
        verbose_name="Payment Type"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD,
        verbose_name="Payment Method"
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS,
        default='pending',
        verbose_name="Payment Status"
    )
    
    # Fee Information
    processing_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Processing Fee"
    )
    net_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Net Amount Received"
    )
    
    # Gateway Information
    gateway_response = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Payment Gateway Response"
    )
    gateway_transaction_id = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Gateway Transaction ID"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Address"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payment_type', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_payment_type_display()} - ${self.amount} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate net amount"""
        if not self.net_amount:
            self.net_amount = self.amount - self.processing_fee
        
        # Auto-set completed_at when status becomes completed
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def mark_as_completed(self, gateway_response=None):
        """Mark payment as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()
        
        # Update user profile if ticket purchase
        if self.payment_type == 'ticket' and self.status == 'completed':
            self.user.profile.total_spent += self.amount
            self.user.profile.games_played += 1
            self.user.profile.save()
        
        return True
    
    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'completed'
    
    @property
    def formatted_amount(self):
        """Format amount with currency symbol"""
        return f"${self.amount:,.2f}"
    
    @property
    def age_in_minutes(self):
        """How many minutes since creation"""
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        return delta.total_seconds() / 60


class GameFinance(models.Model):
    """
    Financial summary for each game.
    
    Tracks sales, fees, profits, and settlement status for each game.
    Updated automatically with each ticket sale and prize payout.
    """
    
    game = models.OneToOneField(
        Game,
        on_delete=models.CASCADE,
        related_name='finance',
        verbose_name="Game"
    )
    
    # Sales Tracking
    total_sales = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name="Total Ticket Sales Amount"
    )
    total_tickets = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Tickets Sold"
    )
    
    # Revenue Distribution
    platform_fee_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name="Total Platform Fee"
    )
    organizer_profit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name="Organizer Profit"
    )
    
    # Prize Management
    total_prize_pool = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name="Total Prize Pool"
    )
    prize_paid_out = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name="Prize Paid to Winners"
    )
    prize_remaining = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name="Unclaimed Prize Money"
    )
    
    # Settlement Status
    prize_paid = models.BooleanField(
        default=False,
        verbose_name="All Prizes Paid"
    )
    fees_settled = models.BooleanField(
        default=False,
        verbose_name="Platform Fees Settled"
    )
    profit_paid = models.BooleanField(
        default=False,
        verbose_name="Organizer Profit Paid"
    )
    settled = models.BooleanField(
        default=False,
        verbose_name="Game Fully Settled"
    )
    
    # Audit Dates
    last_sale_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Ticket Sale"
    )
    prize_settled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Prize Settlement Date"
    )
    profit_paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Profit Payment Date"
    )
    settled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def update_from_sales(self, ticket_price):
        """
        Update financial stats after a new sale.
        """
        from django.utils import timezone
        
        # Update aggregate fields
        self.total_sales = models.F('total_sales') + ticket_price
        self.total_tickets = models.F('total_tickets') + 1
        
        # Calculate fees (simplified, recalculate on save for precision if needed)
        fee_percent = self.game.platform_fee_percent
        fee_amount = (ticket_price * fee_percent) / 100
        
        self.platform_fee_amount = models.F('platform_fee_amount') + fee_amount
        self.organizer_profit = models.F('organizer_profit') + (ticket_price - fee_amount)
        
        self.last_sale_at = timezone.now()
        self.save()
        self.refresh_from_db()  # Refresh to get updated values from F expressions

    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Game Finance"
        verbose_name_plural = "Game Finances"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Finance: {self.game.name} - Sales: ${self.total_sales}"
    
    def update_from_sale(self, ticket_price):
        """Update finance record with new sale"""
        self.total_sales += ticket_price
        self.total_tickets += 1
        
        # Calculate platform fee
        platform_fee = (ticket_price * self.game.platform_fee_percent) / 100
        self.platform_fee_amount += platform_fee
        
        # Calculate organizer profit
        self.organizer_profit += (ticket_price - platform_fee - self.game.prize_amount)
        
        # Update prize pool
        self.total_prize_pool += self.game.prize_amount
        
        self.last_sale_at = timezone.now()
        self.save()
    
    def update_prize_payout(self, amount):
        """Update when prizes are paid"""
        self.prize_paid_out += amount
        self.prize_remaining = self.total_prize_pool - self.prize_paid_out
        
        if self.prize_remaining <= 0:
            self.prize_paid = True
            self.prize_settled_at = timezone.now()
        
        self.check_settlement()
        self.save()
    
    def check_settlement(self):
        """Check if game is fully settled"""
        if (self.prize_paid and self.fees_settled and self.profit_paid and 
            self.prize_remaining <= 0):
            self.settled = True
            self.settled_at = timezone.now()
    
    @property
    def platform_fee_percentage(self):
        """Calculate actual platform fee percentage"""
        if self.total_sales == 0:
            return 0
        return (self.platform_fee_amount / self.total_sales) * 100
    
    @property
    def profit_margin(self):
        """Calculate organizer profit margin"""
        if self.total_sales == 0:
            return 0
        return (self.organizer_profit / self.total_sales) * 100
    
    @property
    def payout_ratio(self):
        """Calculate prize payout ratio"""
        if self.total_sales == 0:
            return 0
        return (self.total_prize_pool / self.total_sales) * 100


class Syndicate(models.Model):
    """
    Group of users pooling money to buy tickets together.
    
    Syndicates increase winning chances by buying multiple tickets
    and splitting winnings among members.
    """
    
    name = models.CharField(
        max_length=100,
        verbose_name="Syndicate Name"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_syndicates',
        verbose_name="Creator"
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='syndicates',
        verbose_name="Game"
    )
    
    # Structure
    max_members = models.PositiveIntegerField(
        default=10,
        verbose_name="Maximum Members"
    )
    ticket_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Total Ticket Price"
    )
    share_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Price per Share"
    )
    total_shares = models.PositiveIntegerField(
        verbose_name="Total Shares Available"
    )
    
    # Numbers
    numbers = models.JSONField(
        verbose_name="Syndicate Numbers",
        help_text="Numbers for syndicate tickets"
    )
    powerball = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Syndicate Powerball"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active Syndicate"
    )
    is_full = models.BooleanField(
        default=False,
        verbose_name="Fully Subscribed"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Syndicate"
        verbose_name_plural = "Syndicates"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Syndicate: {self.name} - {self.game.name}"
    
    @property
    def current_members(self):
        """Get current number of members"""
        return self.members.count()
    
    @property
    def available_shares(self):
        """Calculate available shares"""
        total_purchased = self.members.aggregate(
            total=models.Sum('shares')
        )['total'] or 0
        return self.total_shares - total_purchased
    
    @property
    def fill_percentage(self):
        """Calculate fill percentage"""
        return (self.current_members / self.max_members) * 100


class SyndicateMember(models.Model):
    """
    Member of a syndicate with share allocation.
    
    Links users to syndicates and tracks their share ownership.
    """
    
    syndicate = models.ForeignKey(
        Syndicate,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name="Syndicate"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='syndicate_memberships',
        verbose_name="Member"
    )
    
    shares = models.PositiveIntegerField(
        verbose_name="Shares Owned"
    )
    is_manager = models.BooleanField(
        default=False,
        verbose_name="Syndicate Manager"
    )
    
    # Payment
    paid = models.BooleanField(
        default=False,
        verbose_name="Share Payment Completed"
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Payment Record"
    )
    
    # Winnings
    share_of_winnings = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Share of Winnings"
    )
    winnings_paid = models.BooleanField(
        default=False,
        verbose_name="Winnings Paid"
    )
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Syndicate Member"
        verbose_name_plural = "Syndicate Members"
        unique_together = ('syndicate', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.syndicate.name} ({self.shares} shares)"


class AuditLog(models.Model):
    """
    System audit trail for security and compliance.
    
    Logs important system events, user actions, and administrative changes.
    Essential for debugging, security monitoring, and regulatory compliance.
    """
    
    ACTION_CHOICES = [
        ('user_login', 'User Login'),
        ('user_logout', 'User Logout'),
        ('ticket_purchase', 'Ticket Purchase'),
        ('draw_created', 'Draw Created'),
        ('draw_processed', 'Draw Processed'),
        ('winner_calculated', 'Winner Calculated'),
        ('payout_processed', 'Payout Processed'),
        ('refund_issued', 'Refund Issued'),
        ('game_created', 'Game Created'),
        ('game_updated', 'Game Updated'),
        ('payment_processed', 'Payment Processed'),
        ('admin_action', 'Administrative Action'),
        ('security_event', 'Security Event'),
        ('api_call', 'API Call'),
    ]
    
    LEVEL_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
        ('debug', 'Debug'),
    ]
    
    # Action Details
    action = models.CharField(
        max_length=50, 
        choices=ACTION_CHOICES,
        verbose_name="Action Type"
    )
    level = models.CharField(
        max_length=10,
        choices=LEVEL_CHOICES,
        default='info',
        verbose_name="Log Level"
    )
    description = models.TextField(
        verbose_name="Action Description"
    )
    
    # Actor Information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name="User Who Performed Action"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Address"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )
    
    # Related Objects
    game = models.ForeignKey(
        Game,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Related Game"
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Related Ticket"
    )
    draw = models.ForeignKey(
        Draw,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Related Draw"
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Related Payment"
    )
    
    # Metadata
    metadata = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Additional Metadata"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['action', 'level']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.user or 'System'} - {self.created_at}"


class Wallet(models.Model):
    """
    User wallet for managing funds.
    """
    WALLET_TYPE = [
        ('main', 'Main Wallet'),
        ('bonus', 'Bonus Wallet'),
        ('winnings', 'Winnings Wallet'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    wallet_type = models.CharField(max_length=10, choices=WALLET_TYPE, default='main')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'wallet_type')

