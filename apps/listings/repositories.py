from django.db.models import Count

from .models import Listing, SearchEvent


def catalog():
    return Listing.objects.filter(is_active=True).annotate(
        views=Count("visits", distinct=True),
        reviews=Count("bookings__review", distinct=True),
    )


def popular_queries():
    return SearchEvent.objects.values("keyword").annotate(count=Count("pk")).order_by("-count", "keyword")[:20]
