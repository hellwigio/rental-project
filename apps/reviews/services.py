from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.bookings.models import Booking
from .models import Review


@transaction.atomic
def leave_review(user, booking, **fields):
    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    if booking.renter_id != user.pk:
        raise PermissionDenied()
    if booking.status != Booking.Status.CHECKED_IN or booking.end_date > timezone.localdate():
        raise ValidationError("A completed stay is required.")
    if Review.objects.filter(booking=booking).exists():
        raise ValidationError("This stay already has a review.")
    return Review.objects.create(booking=booking, **fields)
