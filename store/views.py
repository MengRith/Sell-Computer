from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Category, Brand, Product, Cart, CartItem, Wishlist


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def home(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(is_featured=True, is_active=True)
    top_brands = Brand.objects.all()
    return render(request, 'store/home.html', {
        'categories': categories,
        'featured_products': featured_products,
        'top_brands': top_brands,
    })


def category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(is_active=True)
    brands = Brand.objects.filter(products__category=category, products__is_active=True).distinct()

    selected_brand = None
    brand_slug = request.GET.get('brand')
    if brand_slug:
        selected_brand = get_object_or_404(Brand, slug=brand_slug)
        products = products.filter(brand=selected_brand)

    selected_type = request.GET.get('type', '')
    if selected_type and category.slug == 'pc-hardware':
        products = products.filter(pc_type=selected_type)

    sort = request.GET.get('sort', 'default')
    if sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')

    pc_types = Product.PC_TYPE_CHOICES if category.slug == 'pc-hardware' else []

    return render(request, 'store/category.html', {
        'category': category,
        'categories': Category.objects.all(),
        'products': products,
        'brands': brands,
        'selected_brand': selected_brand,
        'selected_type': selected_type,
        'sort': sort,
        'pc_types': pc_types,
    })



def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:4]
    in_wishlist = False
    if request.user.is_authenticated:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        in_wishlist = wishlist.products.filter(pk=product.pk).exists()
    return render(request, 'store/product_detail.html', {
        'product': product,
        'categories': Category.objects.all(),
        'related': related,
        'in_wishlist': in_wishlist,
    })


def search(request):
    q = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=q) | Q(description__icontains=q) | Q(brand__name__icontains=q),
        is_active=True
    ) if q else Product.objects.none()
    return render(request, 'store/search.html', {
        'query': q,
        'products': products,
        'categories': Category.objects.all(),
    })


def cart_view(request):
    return render(request, 'store/cart.html', {
        'cart': get_or_create_cart(request),
        'categories': Category.objects.all(),
    })


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'count': cart.item_count})
    messages.success(request, f'{product.name} added to cart!')
    return redirect('store:cart')


def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    if item.cart == get_or_create_cart(request):
        item.delete()
    return redirect('store:cart')


def update_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    qty = int(request.POST.get('quantity', 1))
    if qty > 0:
        item.quantity = qty
        item.save()
    else:
        item.delete()
    return redirect('store:cart')


def checkout(request):
    cart = get_or_create_cart(request)
    return render(request, 'store/checkout.html', {'cart': cart})


@login_required
def wishlist_view(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'store/wishlist.html', {
        'wishlist': wishlist,
        'categories': Category.objects.all(),
    })


@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    if wishlist.products.filter(pk=product.pk).exists():
        wishlist.products.remove(product)
        added = False
    else:
        wishlist.products.add(product)
        added = True
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'added': added, 'count': wishlist.products.count()})
    return redirect('store:product_detail', slug=product.slug)


def register_view(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('store:home')
    return render(request, 'store/register.html', {
        'form': form,
        'categories': Category.objects.all(),
    })


def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get('next', 'store:home'))
    return render(request, 'store/login.html', {
        'form': form,
        'categories': Category.objects.all(),
    })


def logout_view(request):
    logout(request)
    return redirect('store:home')