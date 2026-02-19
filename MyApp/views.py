from django.shortcuts import render

def home(request):
    return render(request, "home.html")

def find_help(request):
    return render(request, 'find_help.html')