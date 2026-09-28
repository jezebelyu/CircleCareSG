from django.urls import path

from . import views


urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_step_one, name="register"),
    path(
        "register/additional/",
        views.register_step_two,
        name="register_step_two",
    ),
    path(
        "register/review/",
        views.register_review,
        name="register_review",
    ),
]