from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(pre_delete, sender=User)
def delete_user_logs(sender, instance, **kwargs):
    """
    Перед удалением пользователя удаляем его записи в django_admin_log.
    """
    LogEntry.objects.filter(user_id=instance.id).delete()
