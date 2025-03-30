from django.urls import path
from .views import register_user, verify_code, user_login, user_logout

app_name = "authapp"

urlpatterns = [
    path("register/", register_user, name="register_user"),
    path("verify/", verify_code, name="verify_code"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
]
