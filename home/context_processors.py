from django.db.models import Sum
from django.db.models.functions import Coalesce

from .models import Carrito
from django.conf import settings


def cart_counter(request):
    """
    Añade a todas las plantillas:
      - cart_count: número total de unidades en el carrito
      - SITE_DOMAIN: variable global definida en settings.py
    """

    cart_count = 0

    if request.user.is_authenticated:
        carrito = Carrito.objects.filter(cliente=request.user).first()
        if carrito:
            if hasattr(carrito, "cantidad_total_items"):
                cart_count = carrito.cantidad_total_items
            else:
                cart_count = (
                    carrito.carrito_items.aggregate(
                        total=Coalesce(Sum("cantidad"), 0)
                    )["total"]
                    or 0
                )
    else:
        session_cart = request.session.get("cart", {})
        if isinstance(session_cart, dict):
            cart_count = sum(int(v) for v in session_cart.values())

    return {
        "cart_count": cart_count,
        "SITE_DOMAIN": getattr(settings, "SITE_DOMAIN", None),
    }
