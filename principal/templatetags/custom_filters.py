from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def pending_ticket_count(user):
    """Returns the count of pending tickets for a user"""
    if not user.is_authenticated:
        return 0
    return user.ticket_set.filter(status='pending').count()

@register.filter
def sub(value, arg):
    """Subtracts the arg from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


