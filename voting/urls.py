from django.urls import path
from .views import election_results, election_list, election_detail, vote
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("results/<int:election_id>/", election_results, name="election_results"),
    path('elections/<int:election_id>/', election_detail, name='election_detail'),
    path('elections/', election_list, name='election_list'),
    path("", election_list, name="home"),
    path("vote/<int:election_id>/<int:candidate_id>/", vote, name="vote"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
