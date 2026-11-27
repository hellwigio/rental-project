from django_filters import rest_framework as filters

from .models import Listing


class ListingFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="nightly_price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="nightly_price", lookup_expr="lte")
    min_rooms = filters.NumberFilter(field_name="rooms", lookup_expr="gte")
    max_rooms = filters.NumberFilter(field_name="rooms", lookup_expr="lte")
    city = filters.CharFilter(lookup_expr="iexact")
    district = filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Listing
        fields = ["housing_type"]
