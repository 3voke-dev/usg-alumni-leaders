from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from datetime import datetime
from django.db import connection

User = get_user_model()

class Election(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='photos/', default='default-election.jpg', blank=True, null=True)

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("Дата начала должна быть раньше даты окончания")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @staticmethod
    def reset_elections_and_candidates():
        from voting.models import Candidate, Election

        # Удаляем всех кандидатов
        Candidate.objects.all().delete()

        # Удаляем все номинации
        Election.objects.all().delete()

        # Сбрасываем индексацию таблиц
        with connection.cursor() as cursor:
            if connection.vendor == 'sqlite':
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='voting_candidate';")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='voting_election';")
            elif connection.vendor == 'postgresql':
                cursor.execute("ALTER SEQUENCE voting_candidate_id_seq RESTART WITH 1;")
                cursor.execute("ALTER SEQUENCE voting_election_id_seq RESTART WITH 1;")
            elif connection.vendor == 'mysql':
                cursor.execute("ALTER TABLE voting_candidate AUTO_INCREMENT = 1;")
                cursor.execute("ALTER TABLE voting_election AUTO_INCREMENT = 1;")
    
class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="candidates")
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='photos/', default='default-candidate.jpg', blank=True, null=True)

    def __str__(self):
        return self.name
    
    
class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="votes")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="votes")
    user_email = models.EmailField()
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('election', 'user_email')

    def __str__(self):
        return f"Vote: {self.user_email} -> {self.candidate.name}"
