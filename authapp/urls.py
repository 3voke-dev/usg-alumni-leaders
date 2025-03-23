from django.urls import path
from .views import register_user, verify_code

app_name = "authapp"

urlpatterns = [
    path("register/", register_user, name="register_user"),
    path("verify/", verify_code, name="verify_code"),
]
