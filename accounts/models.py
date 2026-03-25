from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrateur'
        DONNEUR = 'donneur', 'Donneur'
        HOPITAL = 'hopital', 'Établissement hospitalier'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.DONNEUR)

    def is_donneur(self):
        return self.role == self.Role.DONNEUR

    def is_hopital(self):
        return self.role == self.Role.HOPITAL

    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
