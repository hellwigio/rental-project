from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.listings.models import Listing
from ..models import Booking

Status = Booking.Status


@transaction.atomic
def reserve(renter, listing, start_date, end_date):
    listing = get_object_or_404(Listing.objects.select_for_update(), pk=listing.pk, is_active=True)
    if not renter.groups.filter(name="renter").exists() or listing.landlord_id == renter.pk:
        raise PermissionDenied("Only a renter can book another owner's listing.")
    if start_date < timezone.localdate() or start_date >= end_date:
        raise ValidationError("Choose a future or current arrival and a later departure.")
    conflicts = listing.bookings.exclude(status__in=[Status.REJECTED, Status.CANCELLED])
    if conflicts.filter(start_date__lt=end_date, end_date__gt=start_date).exists():
        raise ValidationError("Dates already occupied.")
    return Booking.objects.create(listing=listing, renter=renter, start_date=start_date, end_date=end_date)


@transaction.atomic
def change_status(user, booking, target):
    listing = Listing.objects.select_for_update().get(pk=booking.listing_id)
    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    today = timezone.localdate()
    if target == Status.CANCELLED:
        if user.pk != booking.renter_id:
            raise PermissionDenied()
        if booking.status not in (Status.PENDING, Status.CONFIRMED) or today > booking.start_date - timedelta(days=2):
            raise ValidationError("Cancellation unavailable.")
    else:
        if user.pk != listing.landlord_id or not user.groups.filter(name="landlord").exists():
            raise PermissionDenied()
        if target == Status.CHECKED_IN:
            if booking.status != Status.CONFIRMED or not booking.start_date <= today < booking.end_date:
                raise ValidationError("Check-in unavailable.")
        elif target not in (Status.CONFIRMED, Status.REJECTED) or booking.status != Status.PENDING or today >= booking.end_date:
            raise ValidationError("Invalid status transition.")
    booking.status = target
    booking.save(update_fields=["status", "updated_at"])
    return booking
