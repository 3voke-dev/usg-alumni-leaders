from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, F
from django.utils.timezone import now
from .models import Candidate, Vote, Election, Category

def voting_results(request, election_id):
    results = (
        Candidate.objects
        .filter(election_id=election_id)
        .annotate(vote_count=Count('votes'))
        .values('id', 'name', 'vote_count')
    )
    return JsonResponse(list(results), safe=False)

def election_results(request, election_id):
    try:
        results = (
            Vote.objects.filter(election_id=election_id)
            .values(candidate_name=F("candidate__name"))
            .annotate(votes=Count("id"))
        )
        return JsonResponse({"results": list(results)}, safe=False)
    except Election.DoesNotExist:
        return JsonResponse({"error": "Election not found"}, status=404)

def election_list(request):
    elections = Election.objects.filter(is_active=True)
    return render(request, 'landing.html', {'elections': elections, 'user': request.user})

def home(request):
    active_votings = Election.objects.filter(is_active=True)
    return render(request, 'landing.html', {'active_votings': active_votings})

def election_detail(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    candidates = Candidate.objects.filter(election=election)
    return render(request, "elections/detail.html", {"election": election, "candidates": candidates})

def vote(request, election_id, category_id, candidate_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Вы должны быть авторизованы"}, status=401)

    election = get_object_or_404(Election, id=election_id)
    category = get_object_or_404(Category, id=category_id, election=election)
    candidate = get_object_or_404(Candidate, id=candidate_id, election=election)
    
    if Vote.objects.filter(user_email=request.user.email, election=election, category=category).exists():
        return JsonResponse({"error": "Вы уже проголосовали в этой номинации"}, status=400)
    
    Vote.objects.create(user_email=request.user.email, voted_at=now(), candidate=candidate, election=election, category=category)
    return JsonResponse({"message": "Ваш голос учтён"})
