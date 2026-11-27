from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from apps.bookings.models import Booking
from apps.bookings.services import reserve
from apps.listings.models import Listing
from apps.users.models import User


class RentalFlow(APITestCase):
    def account(self, email):
        client = APIClient(enforce_csrf_checks=True)
        credentials = {"email": email, "password": "Strong-demo-password-210!"}
        result = client.post("/api/users/register/", dict(credentials, name="Demo"), format="json")
        self.assertEqual(result.status_code, 201, result.data)
        token = client.get("/api/users/csrf/").data["csrfToken"]
        login = client.post("/api/users/login/", credentials, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(login.status_code, 200)
        client.credentials(HTTP_X_CSRFTOKEN=login.data["csrfToken"])
        return client

    def test_public_catalog_booking_and_review(self):
        owner = self.account("owner@example.com")
        guest = self.account("guest@example.com")
        payload = dict(title="Central studio", description="Near the station", city="Berlin",
                       nightly_price="80.00", rooms=1, housing_type="studio")
        self.assertEqual(owner.post("/api/listings/", payload).status_code, 403)
        self.assertEqual(owner.post("/api/users/landlord/").status_code, 204)
        listing = owner.post("/api/listings/", payload)
        self.assertEqual(listing.status_code, 201, listing.data)
        detail = f"/api/listings/{listing.data['id']}/"
        self.assertEqual(guest.patch(detail, {"title": "Other"}).status_code, 404)
        self.assertEqual(self.client.get(detail).status_code, 200)
        query = self.client.get("/api/listings/", {"search": "station", "city": "Berlin", "max_price": 100})
        self.assertEqual(query.data["count"], 1)
        self.assertEqual(self.client.get("/api/listings/popular/").data[0]["keyword"], "station")
        start = date(2030, 6, 1)
        end = start + timedelta(days=3)
        dates = dict(listing=listing.data["id"], start_date=start, end_date=end)
        with patch("django.utils.timezone.localdate", return_value=start):
            response = guest.post("/api/bookings/", dates)
            self.assertEqual(response.status_code, 201, response.data)
            booking = response.data["id"]
            transition = f"/api/bookings/{booking}/status/"
            self.assertEqual(guest.post("/api/bookings/", dates).status_code, 400)
            self.assertEqual(guest.patch(transition, {"status": "confirmed"}).status_code, 403)
            self.assertEqual(owner.patch(transition, {"status": "confirmed"}).status_code, 200)
            self.assertEqual(owner.patch(transition, {"status": "checked_in"}).status_code, 200)
            review = dict(booking=booking, rating=5, comment="Excellent stay.")
            self.assertEqual(guest.post("/api/reviews/", review).status_code, 400)
        with patch("django.utils.timezone.localdate", return_value=end):
            self.assertEqual(owner.post("/api/reviews/", review).status_code, 403)
            self.assertEqual(guest.post("/api/reviews/", review).status_code, 201)
            self.assertEqual(guest.post("/api/reviews/", review).status_code, 400)
            self.assertEqual(guest.get("/api/bookings/?period=completed").data["count"], 1)
        self.assertEqual(owner.delete(detail).status_code, 400)
        self.assertEqual(owner.patch(detail, {"is_active": False}).status_code, 200)
        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertEqual(guest.post("/api/users/logout/").status_code, 204)


@skipUnless(connection.vendor == "mysql", "Requires MySQL row locks")
class ConcurrentBooking(TransactionTestCase):
    def test_only_one_overlapping_request_succeeds(self):
        owner = User.objects.create_user("owner@example.com", name="Owner")
        guests = [User.objects.create_user(f"guest{i}@example.com", name="Guest") for i in range(2)]
        listing = Listing.objects.create(landlord=owner, title="Flat", city="Berlin", rooms=1,
                                         housing_type="apartment", nightly_price=100)
        barrier = Barrier(2, timeout=10)
        start = date.today() + timedelta(days=7)

        def attempt(guest):
            close_old_connections()
            try:
                barrier.wait()
                reserve(guest, listing, start, start + timedelta(days=2))
                return True
            except ValidationError:
                return False
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(attempt, guests)), [False, True])
        self.assertEqual(Booking.objects.count(), 1)
