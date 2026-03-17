import json
from decimal import Decimal
from functools import wraps

from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .forms import RegisterForm, ReviewForm
from .models import Category, News, Order, OrderItem, Product, Review


@ensure_csrf_cookie
def home(request):
    review_author_name = ""
    if request.user.is_authenticated:
        review_author_name = request.user.get_full_name() or request.user.username

    return render(
        request,
        "meatsite/home.html",
        {
            "review_author_name": review_author_name,
        },
    )


@ensure_csrf_cookie
def register(request):
    if request.user.is_authenticated:
        return redirect("profile")

    return render(request, "meatsite/register.html")


@ensure_csrf_cookie
def login_page(request):
    if request.user.is_authenticated:
        return redirect("profile")

    return render(request, "meatsite/login.html")


@login_required
@ensure_csrf_cookie
def profile(request):
    return render(request, "meatsite/profile.html")


def about(request):
    return render(request, "meatsite/about.html")


def news_detail(request, news_id):
    return render(request, "meatsite/news_detail.html", {"news_id": news_id})


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


@ensure_csrf_cookie
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


def _api_login_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Требуется авторизация"}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapped


def _serialize_order(order):
    created_at_local = timezone.localtime(order.created_at)
    items = []

    for item in order.items.all():
        items.append(
            {
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "item_total": str(item.get_total_price()),
            }
        )

    return {
        "id": order.id,
        "created_at": created_at_local.isoformat(),
        "created_at_display": created_at_local.strftime("%d.%m.%Y %H:%M"),
        "status": order.status,
        "status_display": order.get_status_display(),
        "status_css_class": order.status_css_class,
        "total_price": str(order.get_total_price()),
        "items": items,
    }


def _serialize_review(review):
    created_at_local = timezone.localtime(review.created_at)

    return {
        "id": review.id,
        "rating": review.rating,
        "text": review.text,
        "is_published": review.is_published,
        "created_at": created_at_local.isoformat(),
        "created_at_display": created_at_local.strftime("%d.%m.%Y %H:%M"),
    }


def _serialize_public_review(review):
    return {
        "id": review.id,
        "name": review.name,
        "city": review.city,
        "rating": review.rating,
        "text": review.text,
    }


def _serialize_news_summary(news_item):
    publication_dt = news_item.published_at or news_item.created_at
    publication_dt_local = timezone.localtime(publication_dt)

    return {
        "id": news_item.id,
        "title": news_item.title,
        "short_description": news_item.short_description,
        "preview_text": news_item.short_description or news_item.content[:280],
        "image_url": news_item.image.url if news_item.image else "",
        "published_at": publication_dt_local.isoformat(),
        "published_at_display": publication_dt_local.strftime("%d.%m.%Y"),
        "detail_url": reverse("news_detail", kwargs={"news_id": news_item.id}),
    }


def _serialize_news_detail(news_item):
    publication_dt = news_item.published_at or news_item.created_at
    publication_dt_local = timezone.localtime(publication_dt)

    return {
        "id": news_item.id,
        "title": news_item.title,
        "short_description": news_item.short_description,
        "content": news_item.content,
        "image_url": news_item.image.url if news_item.image else "",
        "published_at": publication_dt_local.isoformat(),
        "published_at_display": publication_dt_local.strftime("%d.%m.%Y %H:%M"),
    }

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
@ensure_csrf_cookie
def api_auth_session(request):
    if not request.user.is_authenticated:
        return JsonResponse({"is_authenticated": False, "user": None})

    return JsonResponse(
        {
            "is_authenticated": True,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "full_name": request.user.get_full_name(),
                "email": request.user.email,
            },
        }
    )


@require_http_methods(["POST"])
def api_auth_register(request):
    payload = _parse_request_json(request)
    if payload is None:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    form = RegisterForm(
        {
            "username": payload.get("username", ""),
            "email": payload.get("email", ""),
            "password1": payload.get("password1", ""),
            "password2": payload.get("password2", ""),
        }
    )

    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    user = form.save()
    login(request, user)

    return JsonResponse(
        {
            "message": "Регистрация прошла успешно",
            "redirect_url": reverse("profile"),
        },
        status=201,
    )


@require_http_methods(["POST"])
def api_auth_login(request):
    payload = _parse_request_json(request)
    if payload is None:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))

    if not username or not password:
        return JsonResponse({"error": "Заполните username и password"}, status=400)

    user = authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({"error": "Неверный логин или пароль"}, status=400)

    login(request, user)
    return JsonResponse({"message": "Вход выполнен", "redirect_url": reverse("profile")})


@require_http_methods(["POST"])
def api_auth_logout(request):
    if request.user.is_authenticated:
        auth_logout(request)

    return JsonResponse({"message": "Выход выполнен", "redirect_url": reverse("home")})


@require_http_methods(["GET", "POST"])
def api_reviews(request):
    if request.method == "GET":
        reviews = Review.objects.filter(is_published=True)[:6]
        return JsonResponse({"results": [_serialize_public_review(review) for review in reviews]})

    payload = _parse_request_json(request)
    if payload is None:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    review_data = {
        "name": payload.get("name", ""),
        "city": payload.get("city", ""),
        "rating": payload.get("rating", ""),
        "text": payload.get("text", ""),
    }

    if request.user.is_authenticated and not str(review_data["name"]).strip():
        review_data["name"] = request.user.get_full_name() or request.user.username

    review_form = ReviewForm(review_data)
    if not review_form.is_valid():
        return JsonResponse({"errors": review_form.errors}, status=400)

    review = review_form.save(commit=False)
    review.is_published = False
    if request.user.is_authenticated:
        review.user = request.user
    review.save()

    return JsonResponse(
        {
            "message": "Спасибо! Отзыв отправлен и появится на сайте после модерации.",
            "review_id": review.id,
        },
        status=201,
    )


@require_http_methods(["GET"])
def api_news(request):
    try:
        limit = min(max(int(request.GET.get("limit", 12)), 1), 50)
    except (TypeError, ValueError):
        limit = 12

    try:
        offset = max(int(request.GET.get("offset", 0)), 0)
    except (TypeError, ValueError):
        offset = 0

    news_qs = News.objects.filter(is_published=True)
    total = news_qs.count()
    news_items = list(news_qs[offset : offset + limit])

    return JsonResponse(
        {
            "results": [_serialize_news_summary(news_item) for news_item in news_items],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total,
            },
        }
    )


@require_http_methods(["GET"])
def api_news_detail(request, news_id):
    news_item = News.objects.filter(id=news_id, is_published=True).first()
    if not news_item:
        return JsonResponse({"error": "Новость не найдена"}, status=404)

    return JsonResponse({"news": _serialize_news_detail(news_item)})


@require_http_methods(["GET"])
@_api_login_required
def api_profile(request):
    user = request.user

    return JsonResponse(
        {
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_full_name(),
                "email": user.email,
            }
        }
    )


@require_http_methods(["GET"])
@_api_login_required
def api_profile_orders(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    return JsonResponse({"results": [_serialize_order(order) for order in orders]})


@require_http_methods(["GET"])
@_api_login_required
def api_profile_reviews(request):
    reviews = Review.objects.filter(user=request.user).order_by("-created_at")

    return JsonResponse({"results": [_serialize_review(review) for review in reviews]})


@require_http_methods(["DELETE"])
@_api_login_required
def api_profile_delete_review(request, review_id):
    review = Review.objects.filter(id=review_id, user=request.user).first()

    if not review:
        return JsonResponse({"error": "Отзыв не найден"}, status=404)

    review.delete()
    return JsonResponse({"message": "Отзыв удален"})


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

