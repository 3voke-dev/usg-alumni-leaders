from django.test import TestCase, Client
from django.contrib.admin.sites import site, AdminSite
from django.core.exceptions import ValidationError
from django.utils.timezone import now, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from voting.models import Election, Candidate, Category, Vote
from voting.admin import ElectionAdmin, CandidateAdmin, VoteAdmin
from django.http import HttpRequest
import csv
from io import StringIO
from datetime import datetime

User = get_user_model()

class VotingModelTests(TestCase):
    def setUp(self):
        """Создаем тестовые данные"""
        self.election = Election.objects.create(
            title="Election 1", 
            is_active=True,
            start_date=timezone.now(),  # Дата начала
            end_date=timezone.now() + timedelta(days=7)  # Дата окончания
        )
        self.category = Category.objects.create(name="Best Developer", election=self.election)
        self.candidate = Candidate.objects.create(name="Alice", election=self.election)

    def test_election_invalid_dates(self):
        """Нельзя создать выборы с датой начала >= даты окончания"""
        election = Election(
            title="Invalid Election",
            start_date=now() + timedelta(days=5),
            end_date=now()
        )
        with self.assertRaises(ValidationError):
            election.full_clean()  # Должен вызвать ValidationError

    def test_unique_vote_per_category(self):
        """Один пользователь не может голосовать дважды в одной категории"""
        Vote.objects.create(
            election=self.election,
            category=self.category,
            candidate=self.candidate,
            user_email="test@example.com"
        )

        with self.assertRaises(IntegrityError):  # Проверяем нарушение unique_together
            Vote.objects.create(
                election=self.election,
                category=self.category,
                candidate=self.candidate,
                user_email="test@example.com"
            )


class VotingViewTests(TestCase):
    def setUp(self):
        """Создаем тестовые выборы, пользователя и кандидатов"""
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password")

        self.election = Election.objects.create(
            title="Election 1", 
            is_active=True,
            start_date=timezone.now(),  # Дата начала
            end_date=timezone.now() + timedelta(days=7)  # Дата окончания
        )
        self.category = Category.objects.create(name="Best Developer", election=self.election)
        self.candidate = Candidate.objects.create(name="Alice", election=self.election)

    def test_voting_results_api(self):
        """API результатов голосования возвращает корректные данные"""
        Vote.objects.create(
            election=self.election,
            category=self.category,
            candidate=self.candidate,
            user_email="test@example.com"
        )

        response = self.client.get(f"/results/{self.election.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice")  # Имя кандидата должно быть в ответе

    def test_vote_auth_required(self):
        """Голосование требует аутентификации"""
        response = self.client.post(f"/vote/{self.election.id}/{self.category.id}/{self.candidate.id}/")
        self.assertEqual(response.status_code, 403)  # Должен быть 403 Forbidden

    def test_vote_success(self):
        """Успешное голосование для аутентифицированного пользователя"""
        self.client.login(username="testuser", password="password")
        response = self.client.post(f"/vote/{self.election.id}/{self.category.id}/{self.candidate.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Vote.objects.count(), 1)  # Проверяем, что голос сохранен


class ElectionAdminTest(TestCase):
    def setUp(self):
        self.election = Election.objects.create(
            title="Election 1", 
            is_active=False,
            start_date=timezone.now(),  # Дата начала
            end_date=timezone.now() + timedelta(days=7)  # Дата окончания
        )
        self.admin = ElectionAdmin(model=Election, admin_site=site)
        self.request = HttpRequest()

    def test_make_votings_active(self):
        self.admin.make_votings_active(self.request, Election.objects.filter(id=self.election.id))
        self.election.refresh_from_db()
        self.assertTrue(self.election.is_active)

    def test_make_votings_inactive(self):
        self.election.is_active = True
        self.election.save()
        self.admin.make_votings_inactive(self.request, Election.objects.filter(id=self.election.id))
        self.election.refresh_from_db()
        self.assertFalse(self.election.is_active)

    def test_reset_votes(self):
        candidate = Candidate.objects.create(name="Candidate 1", election=self.election)
        Vote.objects.create(user_email="test@example.com", candidate=candidate, election=self.election)
        self.assertEqual(Vote.objects.count(), 1)

        self.admin.reset_votes(self.request, Election.objects.filter(id=self.election.id))
        self.assertEqual(Vote.objects.count(), 0)


class CandidateAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.election = Election.objects.create(
            title="Election 1", 
            is_active=True,
            start_date=timezone.now(),  # Дата начала
            end_date=timezone.now() + timedelta(days=7)  # Дата окончания
        )
        self.candidate = Candidate.objects.create(name="Candidate 1", election=self.election)
        self.admin = CandidateAdmin(model=Candidate, admin_site=self.site)
        self.request = HttpRequest()

    def test_export_candidates_to_csv(self):
        response = self.admin.export_candidates_to_csv(self.request, Candidate.objects.all())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

        content = response.content.decode("utf-8")
        reader = csv.reader(StringIO(content))
        rows = list(reader)
        self.assertEqual(rows[0], ["Имя", "Выборы", "Количество голосов"])
        self.assertEqual(rows[1], ["Candidate 1", "Election 1", "0"])


class VoteAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.election = Election.objects.create(
            title="Election 1", 
            is_active=True,
            start_date=timezone.now(),  # Дата начала
            end_date=timezone.now() + timedelta(days=7)  # Дата окончания
        )
        self.category = Category.objects.create(name="Test Category", election=self.election)  # Указываем выборы
        self.candidate = Candidate.objects.create(name="Candidate 1", election=self.election)
        self.vote = Vote.objects.create(
            user_email="test@example.com", 
            candidate=self.candidate, 
            election=self.election,
            category=self.category  # Указываем категорию
        )
        self.admin = VoteAdmin(model=Vote, admin_site=self.site)
        self.request = HttpRequest()
        
    def test_export_votes_to_csv(self):
        response = self.admin.export_votes_to_csv(self.request, Vote.objects.all())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

        content = response.content.decode("utf-8")
        reader = csv.reader(StringIO(content))
        rows = list(reader)
        self.assertEqual(rows[0], ["Email", "Кандидат", "Выборы", "Дата голосования"])
        self.assertEqual(rows[1][:3], ["test@example.com", "Candidate 1", "Election 1"])
