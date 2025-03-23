from django.contrib import admin
from .models import Election, Candidate, Vote
import csv
from django.http import HttpResponse


class CandidateInline(admin.TabularInline):  # Или admin.StackedInline
    model = Candidate
    extra = 1  # Показывать 1 пустую форму для быстрого добавления


@admin.action(description="Сделать выбранные голосования активными")
def make_votings_active(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Сделать выбранные голосования неактивными")
def make_votings_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date", "is_active")
    list_filter = (("start_date", admin.DateFieldListFilter), "is_active")
    search_fields = ("title",)
    ordering = ("-start_date",)
    inlines = [CandidateInline]  # Встраиваем редактирование кандидатов
    actions = ["reset_votes", make_votings_active, make_votings_inactive]  # Добавляем кастомные действия

    @admin.action(description="Сбросить все голоса для выбранных выборов")
    def reset_votes(self, request, queryset):
        for election in queryset:
            Vote.objects.filter(election=election).delete()
        self.message_user(request, "Голоса успешно сброшены!")


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("name", "election", "votes_count")
    list_filter = ("election",)
    search_fields = ("name",)

    def votes_count(self, obj):
        return Vote.objects.filter(candidate=obj).count()

    votes_count.short_description = "Голоса"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("user_email", "candidate", "election", "voted_at")
    list_filter = ("election", "candidate")
    search_fields = ("user_email", "candidate__name")
    ordering = ("-voted_at",)
    actions = ["export_votes_to_csv"]

    @admin.action(description="Экспортировать голоса в CSV")
    def export_votes_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="votes.csv"'
        writer = csv.writer(response)
        writer.writerow(["Email", "Кандидат", "Выборы", "Дата голосования"])

        for vote in queryset:
            writer.writerow([vote.user_email, vote.candidate.name, vote.election.title, vote.voted_at])

        return response
