from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("news/<int:news_id>/", views.news_detail, name="news_detail"),
    path("contacts/", views.contacts, name="contacts"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="meatsite/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("products/", views.products, name="products"),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/increase/<int:product_id>/", views.cart_increase, name="cart_increase"),
    path("cart/decrease/<int:product_id>/", views.cart_decrease, name="cart_decrease"),
    path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("order-success/", views.order_success, name="order_success"),
    path("api/categories/", views.api_categories, name="api_categories"),
    path("api/products/", views.api_products, name="api_products"),
    path("api/cart/", views.api_cart_detail, name="api_cart_detail"),
    path("api/cart/items/", views.api_cart_add_item, name="api_cart_add_item"),
    path("api/cart/items/<int:product_id>/", views.api_cart_update_item, name="api_cart_update_item"),
    path("api/cart/items/<int:product_id>/remove/", views.api_cart_remove_item, name="api_cart_remove_item"),
    path("api/orders/", views.api_create_order, name="api_create_order"),
]
