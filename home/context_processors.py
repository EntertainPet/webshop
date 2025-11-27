from django.db.models import Sum
from django.db.models.functions import Coalesce

from .models import Carrito


def cart_counter(request):
    """
    Añade a todas las plantillas el número total de unidades
    en el carrito del usuario actual.

    - Si el usuario está autenticado: cuenta los ItemCarrito del Carrito asociado al cliente.
    - Si es anónimo: suma las cantidades del carrito almacenado en sesión (request.session['cart']).
    """
    cart_count = 0

    if request.user.is_authenticated:
        # Carrito en base de datos asociado al cliente
        carrito = Carrito.objects.filter(cliente=request.user).first()
        if carrito:
            # Si tu modelo ya tiene la propiedad cantidad_total_items, la aprovechamos
            if hasattr(carrito, "cantidad_total_items"):
                cart_count = carrito.cantidad_total_items
            else:
                # Fallback: sumar cantidades de los items
                cart_count = (
                    carrito.carrito_items.aggregate(
                        total=Coalesce(Sum("cantidad"), 0)
                    )["total"]
                    or 0
                )
    else:
        # Carrito en sesión: {"producto_id-talla_id": cantidad}
        session_cart = request.session.get("cart", {})
        if isinstance(session_cart, dict):
            cart_count = sum(int(v) for v in session_cart.values())

    return {"cart_count": cart_count}