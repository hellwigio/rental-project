from django.db.models import Count

from .models import SearchEvent


def popular_queries():
    return SearchEvent.objects.values("keyword").annotate(count=Count("pk")).order_by("-count", "keyword")[:20]
