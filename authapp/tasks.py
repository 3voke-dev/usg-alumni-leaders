from celery import shared_task
from django.utils.timezone import now
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def delete_unverified_user(user_id):
    try:
        user = User.objects.get(id=user_id)
        if not user.is_verified:
            user.delete()
            return f"User {user_id} deleted"
        return f"User {user_id} already verified"
    except User.DoesNotExist:
        return f"User {user_id} does not exist"
