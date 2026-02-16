from .models import Company

def navigation_context(request):
    return {
        'companies': Company.objects.all()
    }
