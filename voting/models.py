from django.db import models


class Election(models.Model):
    title = models.CharField(max_length=255)  # Название выборов
    description = models.TextField(blank=True, null=True)  # Описание
    start_date = models.DateTimeField()  # Дата начала голосования
    end_date = models.DateTimeField()  # Дата окончания голосования
    is_active = models.BooleanField(default=True)  # Активны ли выборы

    def __str__(self):
        return self.title
    
    
class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="candidates")  # Выборы, к которым относится кандидат
    name = models.CharField(max_length=255)  # Имя кандидата
    bio = models.TextField(blank=True, null=True)  # Описание кандидата
    photo = models.ImageField(upload_to='photos/', default='default.jpg', blank=True, null=True)


    def __str__(self):
        return f"{self.name} ({self.election.title})"
    

class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="votes")  # Выборы
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="votes")  # За кого голос
    user_email = models.EmailField()  # Email пользователя (можно заменить на пользователя, если будет система аутентификации)
    voted_at = models.DateTimeField(auto_now_add=True)  # Когда проголосовал

    class Meta:
        unique_together = ('election', 'user_email')  # Запрет на повторное голосование

    def __str__(self):
        return f"{self.user_email} → {self.candidate.name}"
