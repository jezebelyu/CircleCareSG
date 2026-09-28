from django.shortcuts import render


def home(request):
    return render(request, "mainWebsite/home.html")


def about(request):
    return render(request, "mainWebsite/about.html")


def contact(request):
    return render(request, "mainWebsite/contact.html")


def care_services(request):
    return render(request, "mainWebsite/care_services.html")


def how_it_works(request):
    return render(request, "mainWebsite/how_it_works.html")


def get_involved(request):
    return render(request, "mainWebsite/get_involved.html")