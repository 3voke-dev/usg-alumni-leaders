from django.urls import path
from .views import election_results, election_list
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("results/<int:election_id>/", election_results, name="election_results"),
    path("", election_list, name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
