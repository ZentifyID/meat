from django.contrib import admin
from django.utils import timezone

from .models import Category, News, Product, Review


admin.site.register(Product)
admin.site.register(Category)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "rating", "city", "is_published", "created_at")
    list_filter = ("is_published", "rating", "created_at")
    search_fields = ("name", "city", "text")
    actions = ("mark_published",)

    @admin.action(description="Опубликовать выбранные отзывы")
    def mark_published(self, request, queryset):
        queryset.update(is_published=True)


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "published_at", "created_at")
    list_filter = ("is_published", "created_at", "published_at")
    search_fields = ("title", "short_description", "content")
    actions = ("publish_news", "unpublish_news")

    @admin.action(description="Опубликовать выбранные новости")
    def publish_news(self, request, queryset):
        queryset.update(is_published=True, published_at=timezone.now())

    @admin.action(description="Снять с публикации выбранные новости")
    def unpublish_news(self, request, queryset):
        queryset.update(is_published=False)
