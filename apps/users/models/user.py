from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Group, PermissionsMixin
from django.db import models, router, transaction
from django.utils import timezone


class UserManager(BaseUserManager):
    def get_by_natural_key(self, email):
        return self.get(email=self.normalize_email(email))

    @classmethod
    def normalize_email(cls, email):
        return super().normalize_email(email).lower()

    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        database = self._db or router.db_for_write(self.model)
        with transaction.atomic(using=database):
            user.save(using=database)
            renters, _ = Group.objects.using(database).get_or_create(name="renter")
            user.groups.add(renters)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("A superuser must have is_staff and is_superuser set.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)
