
# Dentro de una aplicación de Django, las funcionalidades se obtienen a través de
# métodos definidos en el archivo “views.py” de la carpeta de la aplicación.

from django.shortcuts import render
from models import Showcase, Item
from django.http import HttpResponse
from django.template import loader

def index(request):
    showcases = Showcase.objects.all()
    showcase = showcases.first()

    items = Item.objects.filter(pk=showcase.item.id)
    item = items.first()
    context = {
        "item_name": item.name,
    }
    template = loader.get_template("index.html")
    return HttpResponse(template.render(context, request))

