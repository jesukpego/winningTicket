from django.contrib.gis.geoip2 import GeoIP2

def get_country_from_ip(request):
    g = GeoIP2()
    ip = request.META.get('REMOTE_ADDR')
    
    try:
        country = g.country(ip)
        return country['country_code']
    except:
        return None
