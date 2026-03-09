from django.shortcuts import render, get_object_or_404
from .models import Product, Category

def home(request):
    return render(request, 'meatsite/home.html')

def about(request):
    return render(request, 'meatsite/about.html')

def products(request):
    products = Product.objects.select_related("category").all()
    categories = Category.objects.all()

    category_id = request.GET.get("category")
    query = request.GET.get("q", "").strip()

    if category_id:
        products = products.filter(category_id=category_id)

    products = list(products)

    if query:
        query_cf = query.casefold()
        products = [
            product for product in products
            if query_cf in product.name.casefold()
        ]

    return render(request, "meatsite/products.html", {
        "products": products,
        "categories": categories,
        "selected_category": category_id,
        "search_query": query,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug)

    similar_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id)[:3]

    return render(request, "meatsite/product_detail.html", {
        "product": product,
        "similar_products": similar_products,
    })

def contacts(request):
    return render(request, 'meatsite/contacts.html')