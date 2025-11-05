
# Dentro de una aplicación de Django, las funcionalidades se obtienen a través de
# métodos definidos en el archivo “views.py” de la carpeta de la aplicación.

from django.shortcuts import render
from .models import Showcase, Item
from django.http import HttpResponse
from django.template import loader

def index(request):
    showcases = Showcase.objects.all()
    showcase = showcases.first()

    if showcase and showcase.item: 
        item = showcase.item
        context = {"item_name": item.name}
    else:
        context = {"item_name": "No item available"}

    template = loader.get_template("index.html")
    return HttpResponse(template.render(context, request))

