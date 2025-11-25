from .models import Carrito


def cart_counter(request):
    """
    Context processor que añade el contador de items del carrito
    a todas las plantillas.
    """
    cart_count = 0
    
    if request.user.is_authenticated:
        try:
            carrito = Carrito.objects.get(cliente=request.user)
            cart_count = carrito.cantidad_total_items
        except Carrito.DoesNotExist:
            cart_count = 0
    else:
        # Contar items en sesión
        session_cart = request.session.get('cart', {})
        cart_count = sum(session_cart.values())
    
    return {'cart_count': cart_count}