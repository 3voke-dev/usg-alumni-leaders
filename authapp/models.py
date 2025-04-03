from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):
    is_verified = models.BooleanField(default=False)  # Проверен ли пользователь
    verification_code = models.PositiveIntegerField(null=True, blank=True)
    verification_code_created_at = models.DateTimeField(null=True, blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name="users",  # Изменил, чтобы избежать конфликта с дефолтным related_name
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="users",  # Изменил для совместимости
        blank=True
    )

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["id"]
