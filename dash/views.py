from django.shortcuts import render
from dash.models import EconomicData, Country
from django.db.models import Max
import os

# Create your views here.
def dash_view(request):
    current_dir = os.path.dirname(__file__)
    svg_path = os.path.join(current_dir, 'static', 'icons', 'icons.svg')
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    return render(request, 'dash.html', {'icons_svg': svg_content})

def accounts_view(request):
    return render(request, 'accounts.html')
