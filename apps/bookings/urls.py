from rest_framework.routers import SimpleRouter

from .views import Bookings

router = SimpleRouter()
router.register("", Bookings, basename="booking")
urlpatterns = router.urls
