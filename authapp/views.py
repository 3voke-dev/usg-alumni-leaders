import random
from django.utils import timezone
from django.contrib.auth import get_user_model, login
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import json
from authapp.tasks import delete_unverified_user


User = get_user_model()

@csrf_exempt
def register_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")

            # Валидация формата email
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({"error": "Неверный формат email"}, status=400)

            # Проверка существования email
            if User.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email уже зарегистрирован"}, status=400)

            verification_code = random.randint(100000, 999999)

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_verified=False,
                verification_code=verification_code,
                verification_code_created_at=timezone.now()
            )

            delete_unverified_user.apply_async((user.id,), countdown=900)

            send_mail(
                "Код подтверждения регистрации",
                f"Ваш код подтверждения: {verification_code}",
                "noreply@yourdomain.com",
                [email],
                fail_silently=False,
            )

            return JsonResponse({
                "message": "Код отправлен на почту!\n Проверьте папку спам.",
                "email": email
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Невалидный JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Некорректный запрос"}, status=400)

@csrf_exempt
def verify_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        code = data.get("code")

        try:
            user = User.objects.get(email=email, verification_code=int(code))
            
            # Добавляем проверку времени
            from django.utils import timezone
            time_difference = timezone.now() - user.verification_code_created_at
            if time_difference.seconds > 900:  # 15 минут = 900 секунд
                return JsonResponse({"error": "Код просрочен"}, status=400)

            user.is_verified = True
            user.verification_code = None
            user.verification_code_created_at = None  # Очищаем временную метку
            user.save()

            login(request, user)
            return JsonResponse({"success": True})

        except User.DoesNotExist:
            return JsonResponse({"error": "Неверный код"}, status=400)
        except ValueError:  # Добавляем обработку нечисловых кодов
            return JsonResponse({"error": "Неверный формат кода"}, status=400)

    return JsonResponse({"error": "Некорректный запрос"}, status=400)
