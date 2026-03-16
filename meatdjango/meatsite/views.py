import json
from decimal import Decimal

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

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


@ensure_csrf_cookie
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


@ensure_csrf_cookie
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


@ensure_csrf_cookie
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


@ensure_csrf_cookie
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


def _parse_request_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None


def _normalize_cart(cart):
    normalized_cart = {}

    for product_id, item in cart.items():
        try:
            product_id_int = int(product_id)
            quantity = int(item.get("quantity", 0))
        except (TypeError, ValueError, AttributeError):
            continue

        if quantity > 0:
            normalized_cart[str(product_id_int)] = {"quantity": quantity}

    return normalized_cart


def _get_cart(request):
    cart = request.session.get("cart", {})
    normalized_cart = _normalize_cart(cart)

    if normalized_cart != cart:
        request.session["cart"] = normalized_cart

    return normalized_cart


def _serialize_product(request, product):
    return {
        "id": product.id,
        "slug": product.slug,
        "name": product.name,
        "description": product.description,
        "price": str(product.price),
        "available": product.available,
        "category": {
            "id": product.category_id,
            "name": product.category.name,
            "slug": product.category.slug,
        },
        "image_url": product.image.url if product.image else "",
        "detail_url": reverse("product_detail", kwargs={"slug": product.slug}),
    }


def _build_cart_payload(request):
    cart = _get_cart(request)
    product_ids = [int(product_id) for product_id in cart.keys()]
    products_by_id = Product.objects.select_related("category").in_bulk(product_ids)

    items = []
    total_price = Decimal("0")
    total_count = 0

    for product_id, item in cart.items():
        product = products_by_id.get(int(product_id))
        if not product:
            continue

        quantity = item["quantity"]
        item_total = product.price * quantity

        items.append(
            {
                "product": _serialize_product(request, product),
                "quantity": quantity,
                "item_total": str(item_total),
            }
        )

        total_price += item_total
        total_count += quantity

    return {
        "items": items,
        "total_price": str(total_price),
        "total_count": total_count,
    }


@require_http_methods(["GET"])
def api_categories(request):
    categories = Category.objects.all().values("id", "name", "slug")
    return JsonResponse({"results": list(categories)})


@require_http_methods(["GET"])
def api_products(request):
    products_qs = Product.objects.select_related("category").all()

    category_id = request.GET.get("category")
    search_query = request.GET.get("q", "").strip()

    if category_id:
        products_qs = products_qs.filter(category_id=category_id)

    products_list = list(products_qs)

    if search_query:
        query_cf = search_query.casefold()
        products_list = [product for product in products_list if query_cf in product.name.casefold()]

    return JsonResponse({"results": [_serialize_product(request, product) for product in products_list]})


@require_http_methods(["GET"])
def api_cart_detail(request):
    return JsonResponse(_build_cart_payload(request))


@require_http_methods(["POST"])
def api_cart_add_item(request):
    payload = _parse_request_json(request)
    if payload is None:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    product_id = payload.get("product_id")
    quantity = payload.get("quantity", 1)

    try:
        product_id = int(product_id)
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Неверный product_id или quantity"}, status=400)

    product = Product.objects.filter(id=product_id, available=True).first()
    if not product:
        return JsonResponse({"error": "Товар не найден или недоступен"}, status=404)

    cart = _get_cart(request)
    product_id_str = str(product.id)

    if product_id_str in cart:
        cart[product_id_str]["quantity"] += quantity
    else:
        cart[product_id_str] = {"quantity": quantity}

    request.session["cart"] = cart

    return JsonResponse({"message": "Товар добавлен в корзину", "cart": _build_cart_payload(request)}, status=201)


@require_http_methods(["PATCH"])
def api_cart_update_item(request, product_id):
    payload = _parse_request_json(request)
    if payload is None:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    try:
        quantity = int(payload.get("quantity"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Неверный quantity"}, status=400)

    cart = _get_cart(request)
    product_id_str = str(product_id)

    if product_id_str not in cart:
        return JsonResponse({"error": "Товар не найден в корзине"}, status=404)

    if quantity <= 0:
        del cart[product_id_str]
    else:
        cart[product_id_str]["quantity"] = quantity

    request.session["cart"] = cart
    return JsonResponse({"message": "Корзина обновлена", "cart": _build_cart_payload(request)})


@require_http_methods(["DELETE"])
def api_cart_remove_item(request, product_id):
    cart = _get_cart(request)
    product_id_str = str(product_id)

    if product_id_str not in cart:
        return JsonResponse({"error": "Товар не найден в корзине"}, status=404)

    del cart[product_id_str]
    request.session["cart"] = cart

    return JsonResponse({"message": "Товар удален из корзины", "cart": _build_cart_payload(request)})


@require_http_methods(["POST"])
def api_create_order(request):
    cart_payload = _build_cart_payload(request)

    if not cart_payload["items"]:
        return JsonResponse({"error": "Корзина пуста"}, status=400)

    payload = _parse_request_json(request)
    if payload is None:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    full_name = (payload.get("full_name") or "").strip()
    phone = (payload.get("phone") or "").strip()
    email = (payload.get("email") or "").strip() or None
    address = (payload.get("address") or "").strip()

    if not full_name or not phone or not address:
        return JsonResponse(
            {"error": "Заполните обязательные поля: full_name, phone, address"},
            status=400,
        )

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        full_name=full_name,
        phone=phone,
        email=email,
        address=address,
        is_paid=True,
    )

    for item in cart_payload["items"]:
        OrderItem.objects.create(
            order=order,
            product_id=item["product"]["id"],
            quantity=item["quantity"],
        )

    request.session["cart"] = {}

    return JsonResponse(
        {
            "message": "Заказ оформлен",
            "order_id": order.id,
            "redirect_url": reverse("order_success"),
        },
        status=201,
    )
