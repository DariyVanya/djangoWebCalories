from django.shortcuts import render

# Create your views here.
def today(request):
    return render(request, "today/today.html")