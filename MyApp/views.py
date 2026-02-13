from django.shortcuts import render

def home(request):
    return render(request, "home.html")

def resources(request):
    return render(request, "resources.html")