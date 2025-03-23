import random
from django.contrib.auth import get_user_model, login
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from authapp.tasks import delete_unverified_user

User = get_user_model()

@csrf_exempt
def register_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email уже зарегистрирован"}, status=400)

        verification_code = random.randint(100000, 999999)

        user = User.objects.create_user(username=username, email=email, password=password, is_verified=False)
        user.verification_code = verification_code
        user.save()

        delete_unverified_user.apply_async((user.id,), countdown=60) # 900

        send_mail(
            "Код подтверждения регистрации",
            f"Ваш код подтверждения: {verification_code}",
            "noreply@yourdomain.com",
            [email],
            fail_silently=False,
        )

        return JsonResponse({"message": "Код отправлен на почту!\n Проверьте папку спам.", "email": email})

    return JsonResponse({"error": "Некорректный запрос"}, status=400)

@csrf_exempt
def verify_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        code = data.get("code")

        try:
            user = User.objects.get(email=email, verification_code=int(code))
            user.is_verified = True
            user.verification_code = None
            user.save()

            login(request, user)  # Автоматически авторизуем пользователя

            return JsonResponse({"success": True})

        except User.DoesNotExist:
            return JsonResponse({"error": "Неверный код"}, status=400)

    return JsonResponse({"error": "Некорректный запрос"}, status=400)
