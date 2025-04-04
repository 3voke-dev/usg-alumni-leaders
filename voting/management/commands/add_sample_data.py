from django.core.management.base import BaseCommand
from voting.models import Election, Candidate

class Command(BaseCommand):
    help = "Добавить 9 номинаций с 5 кандидатами в каждой"

    def handle(self, *args, **kwargs):
        # Удаляем существующие данные
        Election.reset_elections_and_candidates()

        # Добавляем 9 номинаций
        for i in range(1, 10):
            election = Election.objects.create(
                title=f"Номинация {i}",
                description=f"Описание для номинации {i}",
                start_date="2025-01-01 00:00:00",
                end_date="2025-12-31 23:59:59",
                is_active=True,
            )

            # Добавляем 5 кандидатов для каждой номинации
            for j in range(1, 6):
                Candidate.objects.create(
                    election=election,
                    name=f"Кандидат {j} для Номинации {i}",
                    bio=f"Биография кандидата {j} для Номинации {i}",
                )

        self.stdout.write(self.style.SUCCESS("Успешно добавлены 9 номинаций с 5 кандидатами в каждой."))
