from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("care-services/", views.care_services, name="care_services"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("get-involved/", views.get_involved, name="get_involved"),
    path("contact/", views.contact, name="contact"),
]