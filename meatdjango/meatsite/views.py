from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import RegisterForm, ReviewForm
from .models import Category, News, Order, OrderItem, Product, Review


def home(request):
    initial = {}
    if request.user.is_authenticated:
        initial["name"] = request.user.get_full_name() or request.user.username

    review_form = ReviewForm(initial=initial)
    review_submitted = request.GET.get("review_submitted") == "1"

    if request.method == "POST":
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.is_published = False
            if request.user.is_authenticated:
                review.user = request.user
            review.save()
            return redirect(f"{reverse('home')}?review_submitted=1#reviews")

    reviews = Review.objects.filter(is_published=True)[:6]

    return render(
        request,
        "meatsite/home.html",
        {
            "reviews": reviews,
            "review_form": review_form,
            "review_submitted": review_submitted,
        },
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("profile")

    form = RegisterForm()
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("profile")

    return render(request, "meatsite/register.html", {"form": form})


@login_required
def profile(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )
    reviews = Review.objects.filter(user=request.user).order_by("-created_at")

    return render(
        request,
        "meatsite/profile.html",
        {
            "orders": orders,
            "reviews": reviews,
        },
    )


def about(request):
    news_items = News.objects.filter(is_published=True)[:12]
    return render(request, "meatsite/about.html", {"news_items": news_items})


def news_detail(request, news_id):
    news_item = get_object_or_404(News, id=news_id, is_published=True)
    return render(request, "meatsite/news_detail.html", {"news_item": news_item})


def contacts(request):
    return render(request, "meatsite/contacts.html")


def products(request):
    products_qs = Product.objects.select_related("category").all()
    categories = Category.objects.all()

    category_id = request.GET.get("category")
    query = request.GET.get("q", "").strip()

    if category_id:
        products_qs = products_qs.filter(category_id=category_id)

    products_list = list(products_qs)

    if query:
        query_cf = query.casefold()
        products_list = [product for product in products_list if query_cf in product.name.casefold()]

    return render(
        request,
        "meatsite/products.html",
        {
            "products": products_list,
            "categories": categories,
            "selected_category": category_id,
            "search_query": query,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug)

    similar_products = Product.objects.filter(category=product.category, available=True).exclude(id=product.id)[:3]

    return render(
        request,
        "meatsite/product_detail.html",
        {
            "product": product,
            "similar_products": similar_products,
        },
    )


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})
    product_id_str = str(product.id)

    if product_id_str in cart:
        cart[product_id_str]["quantity"] += 1
    else:
        cart[product_id_str] = {"quantity": 1}

    request.session["cart"] = cart
    return redirect(request.META.get("HTTP_REFERER", "products"))


def cart_detail(request):
    cart = request.session.get("cart", {})
    cart_items = []
    total_price = 0

    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)
        quantity = item["quantity"]
        item_total = product.price * quantity

        cart_items.append(
            {
                "product": product,
                "quantity": quantity,
                "item_total": item_total,
            }
        )

        total_price += item_total

    return render(
        request,
        "meatsite/cart.html",
        {
            "cart_items": cart_items,
            "total_price": total_price,
        },
    )


def cart_increase(request, product_id):
    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        cart[product_id_str]["quantity"] += 1

    request.session["cart"] = cart
    return redirect("cart_detail")


def cart_decrease(request, product_id):
    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        cart[product_id_str]["quantity"] -= 1
        if cart[product_id_str]["quantity"] <= 0:
            del cart[product_id_str]

    request.session["cart"] = cart
    return redirect("cart_detail")


def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]

    request.session["cart"] = cart
    return redirect("cart_detail")


def checkout(request):
    cart = request.session.get("cart", {})

    if not cart:
        return redirect("cart_detail")

    cart_items = []
    total_price = 0

    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)
        quantity = item["quantity"]
        item_total = product.price * quantity

        cart_items.append(
            {
                "product": product,
                "quantity": quantity,
                "item_total": item_total,
            }
        )

        total_price += item_total

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        address = request.POST.get("address")

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            phone=phone,
            email=email,
            address=address,
            is_paid=True,
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
            )

        request.session["cart"] = {}
        return redirect("order_success")

    return render(
        request,
        "meatsite/checkout.html",
        {
            "cart_items": cart_items,
            "total_price": total_price,
        },
    )


def order_success(request):
    return render(request, "meatsite/order_success.html")
