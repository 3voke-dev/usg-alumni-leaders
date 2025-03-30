from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.models import LogEntry
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):  # Используем UserAdmin для корректной работы
    list_display = ("id", "username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")

    def delete_queryset(self, request, queryset):
        # Удаляем логи, чтобы не было ссылок на несуществующих пользователей
        LogEntry.objects.filter(user_id__in=queryset.values_list("id", flat=True)).delete()
        # Теперь можно удалять пользователей
        super().delete_queryset(request, queryset)
    

    def delete_model(self, request, obj):
        """
        Удаляем пользователя и его логи.
        """
        from django.contrib.admin.models import LogEntry
        LogEntry.objects.filter(user_id=obj.id).delete()
        super().delete_model(request, obj)
