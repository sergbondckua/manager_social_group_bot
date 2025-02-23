from django.contrib import admin

from common.admin import BaseAdmin
from .models import MonoBankClient, MonoBankCard
from .forms import MonoBankCardAdminForm


@admin.register(MonoBankClient)
class MonoBankClientAdmin(admin.ModelAdmin):
    list_display = ["name", "client_token"]


@admin.register(MonoBankCard)
class MonoBankCardAdmin(admin.ModelAdmin):
    form = MonoBankCardAdminForm
    list_display = ["client", "card_id", "is_active"]
    list_filter = ["client", "is_active"]
    search_fields = ["client__name", "card_id"]
    actions = ["make_active", "make_inactive"]
    readonly_fields = ("id", "created_at", "updated_at")
    save_as = True
    save_on_top = True
    save_as_continue = True
    fieldsets = (
        ("Основні дані", {"fields": ("client", "card_id", "is_active")}),
    ) + BaseAdmin.fieldsets

    @admin.action(description="✅ Активувати вибрані картки")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="❎ Деактивувати вибрані картки")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    class Media:
        js = ("adminpanel/js/admin.js",)
