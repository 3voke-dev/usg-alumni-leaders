import json
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from unittest.mock import patch
from .tasks import delete_unverified_user

User = get_user_model()


class AuthTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_email = "test@example.com"
        self.test_password = "TestPass123"
        self.user_data = {
            "username": "testuser",
            "email": self.test_email,
            "password": self.test_password
        }

    def test_successful_registration(self):
        """Тест успешной регистрации и отправки кода"""
        response = self.client.post(
            '/auth/register/',
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Код отправлен", response.json()['message'])

        user = User.objects.get(email=self.test_email)
        self.assertIsNotNone(user.verification_code)
        self.assertFalse(user.is_verified)

    def test_email_already_registered(self):
        """Тест повторной регистрации"""
        User.objects.create_user(**self.user_data)
        response = self.client.post(
            '/auth/register/',
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], "Email уже зарегистрирован")

    def test_successful_verification(self):
        """Тест успешного подтверждения кода"""
        user = User.objects.create_user(**self.user_data, verification_code=123456)
        user.verification_code_created_at = timezone.now()
        user.save()

        response = self.client.post(
            '/auth/verify/',
            data=json.dumps({"email": self.test_email, "code": 123456}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        user.refresh_from_db()
        self.assertTrue(user.is_verified)
        self.assertIsNone(user.verification_code)
        self.assertIsNone(user.verification_code_created_at)

    def test_expired_code(self):
        """Тест просроченного кода"""
        user = User.objects.create_user(**self.user_data, verification_code=123456)
        user.verification_code_created_at = timezone.now() - timedelta(minutes=16)
        user.save()

        response = self.client.post(
            '/auth/verify/',
            data=json.dumps({"email": self.test_email, "code": 123456}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], "Код просрочен")

    def test_wrong_code(self):
        """Тест неверного кода"""
        User.objects.create_user(**self.user_data, verification_code=123456)
        
        response = self.client.post(
            '/auth/verify/',
            data=json.dumps({"email": self.test_email, "code": 000000}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], "Неверный код")

    def test_invalid_code_format(self):
        """Тест нечислового кода"""
        response = self.client.post(
            '/auth/verify/',
            data=json.dumps({"email": self.test_email, "code": "abcdef"}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], "Неверный формат кода")

    def test_automatic_login_after_verification(self):
        """Тест автоматической авторизации после подтверждения"""
        user = User.objects.create_user(**self.user_data, verification_code=123456)
        user.verification_code_created_at = timezone.now()
        user.save()

        response = self.client.post(
            '/auth/verify/',
            data=json.dumps({"email": self.test_email, "code": 123456}),
            content_type='application/json'
        )
        
        auth_user = response.wsgi_request.user
        self.assertTrue(auth_user.is_authenticated)
        self.assertEqual(auth_user.email, self.test_email)

    @patch('authapp.tasks.delete_unverified_user.apply_async')
    def test_user_deletion_by_celery(self, mock_task):
        """Тест задачи удаления неподтвержденных пользователей"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123",
            verification_code=123456,
            verification_code_created_at=timezone.now() - timedelta(minutes=16)
        )
        
        delete_unverified_user.apply_async((user.id,), countdown=900)
        
        mock_task.assert_called_once_with((user.id,), countdown=900)


class DeleteUnverifiedUserTaskTest(TestCase):
    def test_delete_unverified_user(self):
        user = User.objects.create(email="test@example.com", is_verified=False)
        result = delete_unverified_user(user.id)
        self.assertEqual(result, f"User {user.id} deleted")
        self.assertFalse(User.objects.filter(id=user.id).exists())

    def test_dont_delete_verified_user(self):
        user = User.objects.create(email="verified@example.com", is_verified=True)
        result = delete_unverified_user(user.id)
        self.assertEqual(result, f"User {user.id} already verified")
        self.assertTrue(User.objects.filter(id=user.id).exists())

    def test_delete_nonexistent_user(self):
        result = delete_unverified_user(99999)
        self.assertEqual(result, "User 99999 does not exist")