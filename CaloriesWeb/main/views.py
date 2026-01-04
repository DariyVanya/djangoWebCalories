from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from .forms import LogInForm, SignUpForm

def index(request):
    print(request.user)

    return render(request, "main/index.html")

def about(request):
    return render(request, "main/about.html")

def report(request):
    return render(request, "main/report.html")

def logIn(request):
    if request.method == 'POST':
        form = LogInForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, 'Невірний логін або пароль')
    else:
        form = LogInForm()

    return render(request, "main/logIn.html", {'form': form})

def signUp(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()

            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']

            user = authenticate(request, username=username, password=password)
            login(request, user)

            return redirect('home')
        else:
            print(form.errors)
    else:
        form = SignUpForm()

    return render(request, "main/signUp.html", {'form': form})



def logOut(request):
    logout(request)
    return redirect('home')