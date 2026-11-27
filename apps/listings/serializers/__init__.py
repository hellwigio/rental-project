from decimal import Decimal

from rest_framework import serializers

from ..models import Listing


class ListingSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True)
    nightly_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    rooms = serializers.IntegerField(min_value=1, max_value=32767)

    class Meta:
        model = Listing
        fields = "__all__"
        read_only_fields = ["landlord"]
