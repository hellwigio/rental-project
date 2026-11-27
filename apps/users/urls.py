from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.CsrfToken.as_view()),
    path("register/", views.Register.as_view()),
    path("login/", views.Login.as_view()),
    path("logout/", views.Logout.as_view()),
    path("landlord/", views.BecomeLandlord.as_view()),
]
