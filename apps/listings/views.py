from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from . import repositories
from .filters import ListingFilter
from .models import Listing, ListingView, SearchEvent
from .serializers import ListingSerializer


class CatalogOrdering(filters.OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        fields = {term.lstrip("-") for term in ordering}
        metrics = {"views": "visits", "reviews": "bookings__review"}
        annotations = {
            field: Count(relation, distinct=True)
            for field, relation in metrics.items() if field in fields
        }
        return queryset.annotate(**annotations).order_by(*ordering)


class Listings(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, CatalogOrdering]
    filterset_class = ListingFilter
    search_fields = ["title", "description"]
    ordering_fields = ["nightly_price", "created_at", "views", "reviews"]
    ordering = ["-created_at", "-pk"]

    def get_queryset(self):
        if self.action in {"list", "retrieve"}:
            return Listing.objects.filter(is_active=True)
        return Listing.objects.filter(landlord=self.request.user).order_by("-pk")

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset) if self.action == "list" else queryset

    def list(self, request, *args, **kwargs):
        keyword = request.query_params.get("search", "").strip().casefold()
        if len(keyword) > 200:
            raise ValidationError({"search": "Maximum 200 characters."})
        response = super().list(request, *args, **kwargs)
        if keyword:
            SearchEvent.objects.create(keyword=keyword, user=request.user if request.user.is_authenticated else None)
        return response

    def retrieve(self, request, *args, **kwargs):
        listing = self.get_object()
        ListingView.objects.create(listing=listing, user=request.user if request.user.is_authenticated else None)
        return Response(self.get_serializer(listing).data)

    def perform_create(self, serializer):
        if not self.request.user.groups.filter(name="landlord").exists():
            raise PermissionDenied("Landlord membership required.")
        serializer.save(landlord=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def mine(self, request):
        page = self.paginate_queryset(self.get_queryset())
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ValidationError("This listing has bookings. Set is_active to false.") from exc

    @action(detail=False, methods=["get"])
    def popular(self, request):
        return Response(list(repositories.popular_queries()))
