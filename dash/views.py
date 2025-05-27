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
    return render(request, 'index.html', {'indicators': data})