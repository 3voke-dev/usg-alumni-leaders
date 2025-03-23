from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count
from .models import Candidate, Vote, Election
from django.utils import timezone


def voting_results(request, election_id):
    results = (
        Candidate.objects
        .filter(election_id=election_id)
        .annotate(vote_count=Count('vote'))
        .values('id', 'name', 'vote_count')
    )
    return JsonResponse(list(results), safe=False)


def election_results(request, election_id): 
    election = get_object_or_404(Election, id=election_id)
    candidates = Candidate.objects.filter(election=election)

    results = []
    for candidate in candidates:
        votes_count = Vote.objects.filter(candidate=candidate).count()
        results.append({
            "candidate": candidate,
            "votes": votes_count
        })

    return render(request, "elections/results.html", {
        "election": election,
        "candidates": candidates,
        "results": results
    })


def election_list(request):
    elections = Election.objects.filter(is_active=True)
    return render(request, 'landing.html', {
        'elections': elections,
        'user': request.user
    })

def home(request):
    active_votings = Vote.objects.filter(is_active=True)  # Фильтруем активные голосования
    return render(request, 'landing.html', {'active_votings': active_votings})

def election_detail(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    candidates = Candidate.objects.filter(election=election)

    return render(request, "elections/detail.html", {
        "election": election,
        "candidates": candidates
    })