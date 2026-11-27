from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import Credentials, Registration


class CsrfToken(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class Register(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = Registration(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except IntegrityError as exc:
            raise ValidationError({"email": "Email already registered."}) from exc
        return Response(serializer.data, status=201)


@method_decorator(csrf_protect, name="dispatch")
class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = Credentials(data=request.data)
        data.is_valid(raise_exception=True)
        user = authenticate(request=request, **data.validated_data)
        if user is None:
            raise ValidationError("Invalid credentials.")
        login(request, user)
        return Response({"id": user.pk, "csrfToken": get_token(request)})


class Logout(APIView):
    def post(self, request):
        logout(request)
        return Response(status=204)


class BecomeLandlord(APIView):
    def post(self, request):
        request.user.groups.add(Group.objects.get(name="landlord"))
        return Response(status=204)
