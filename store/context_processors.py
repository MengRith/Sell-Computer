from .models import Cart

def cart_count(request):
    count = 0
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            sk = request.session.session_key
            cart = Cart.objects.filter(session_key=sk).first() if sk else None
        if cart:
            count = cart.item_count
    except:
        pass
    return {'cart_count': count}