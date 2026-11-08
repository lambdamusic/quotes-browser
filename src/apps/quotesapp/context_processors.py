from django.conf import settings


def site_url(request):
    """SITE_URL for canonical links and other absolute URLs (see settings.py)"""
    return {'SITE_URL': settings.SITE_URL}
