from django.shortcuts import render
from dash.models import EconomicData, Country
from django.db.models import Max


# Create your views here.
def dash_view(request):
    vietnam = Country.objects.get(name="Vietnam")
    latest_dates = EconomicData.objects.filter(country=vietnam).values('indicator').annotate(latest=Max('date'))

    data = []
    for row in latest_dates:
        ed = EconomicData.objects.get(country=vietnam, indicator=row['indicator'], date=row['latest'])
        data.append(ed)
    return render(request, 'dash.html', {'indicators': data, 'page_title': 'Dashboard',
        'page_subtitle': 'Manage Your Site',})


def pages_view(request):
    return render(request, 'pages.html')

def posts_view(request):
    return render(request, 'posts.html')

def users_view(request):
    return render(request, 'users.html')

def login_view(request):
    return render(request, 'login.html')

def edit_view(request):
    return render(request, 'edit.html')