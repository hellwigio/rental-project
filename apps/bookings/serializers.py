from rest_framework import serializers

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ["status", "renter"]


class StatusChange(serializers.Serializer):
    status = serializers.ChoiceField(choices=Booking.Status.choices)
