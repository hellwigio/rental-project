from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from . import services
from .models import Booking
from .serializers import BookingSerializer, StatusChange


class Bookings(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = BookingSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Booking.objects.filter(Q(renter=user) | Q(listing__landlord=user)).order_by("-start_date", "-pk")
        period = self.request.query_params.get("period") if self.action == "list" else None
        if period == "completed":
            return qs.filter(end_date__lte=timezone.localdate(), status=Booking.Status.CHECKED_IN)
        if period == "active":
            return qs.filter(end_date__gt=timezone.localdate()).exclude(
                status__in=[Booking.Status.CANCELLED, Booking.Status.REJECTED]
            )
        if period:
            raise ValidationError({"period": "Choose active or completed."})
        return qs

    def perform_create(self, serializer):
        serializer.instance = services.reserve(self.request.user, **serializer.validated_data)

    @action(detail=True, methods=["patch"], url_path="status")
    def transition(self, request, pk=None):
        change = StatusChange(data=request.data)
        change.is_valid(raise_exception=True)
        booking = services.change_status(request.user, self.get_object(), change.validated_data["status"])
        return Response(self.get_serializer(booking).data)
