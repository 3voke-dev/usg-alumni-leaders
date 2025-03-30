from django.contrib import admin
from .models import Election, Candidate, Vote
import csv
from django.http import HttpResponse
from openpyxl import Workbook


class CandidateInline(admin.TabularInline):  # Или admin.StackedInline
    model = Candidate
    extra = 1  # Показывать 1 пустую форму для быстрого добавления


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date", "is_active")
    list_filter = (("start_date", admin.DateFieldListFilter), "is_active")
    search_fields = ("title",)
    ordering = ("-start_date",)
    inlines = [CandidateInline]
    actions = ["reset_votes", "make_votings_active", "make_votings_inactive"]  # <-- Теперь все методы внутри класса

    @admin.action(description="Сделать выбранные голосования активными")
    def make_votings_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Сделать выбранные голосования неактивными")
    def make_votings_inactive(self, request, queryset):
        queryset.update(is_active=False)

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
    actions = ["export_candidates_to_csv", "export_candidates_to_excel"]

    def votes_count(self, obj):
        return Vote.objects.filter(candidate=obj).count()

    votes_count.short_description = "Голоса"

    @admin.action(description="Экспортировать кандидатов в CSV")
    def export_candidates_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="candidates.csv"'
        writer = csv.writer(response)
        writer.writerow(["Имя", "Выборы", "Количество голосов"])

        for candidate in queryset:
            writer.writerow([candidate.name, candidate.election.title, self.votes_count(candidate)])

        return response

    @admin.action(description="Экспортировать кандидатов в Excel")
    def export_candidates_to_excel(self, request, queryset):
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="candidates.xlsx"'
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Кандидаты"
        sheet.append(["Имя", "Выборы", "Количество голосов"])

        for candidate in queryset:
            sheet.append([candidate.name, candidate.election.title, self.votes_count(candidate)])

        workbook.save(response)
        return response


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("user_email", "candidate", "election", "voted_at")
    list_filter = ("election", "candidate")
    search_fields = ("user_email", "candidate__name")
    ordering = ("-voted_at",)
    actions = ["export_votes_to_csv", "export_votes_to_excel"]

    @admin.action(description="Экспортировать голоса в CSV")
    def export_votes_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="votes.csv"'
        writer = csv.writer(response)
        writer.writerow(["Email", "Кандидат", "Выборы", "Дата голосования"])

        for vote in queryset:
            writer.writerow([vote.user_email, vote.candidate.name, vote.election.title, vote.voted_at])

        return response

    @admin.action(description="Экспортировать голоса в Excel")
    def export_votes_to_excel(self, request, queryset):
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="votes.xlsx"'
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Голоса"
        sheet.append(["Email", "Кандидат", "Выборы", "Дата голосования"])

        for vote in queryset:
            sheet.append([vote.user_email, vote.candidate.name, vote.election.title, vote.voted_at])

        workbook.save(response)
        return response
