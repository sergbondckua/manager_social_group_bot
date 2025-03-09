from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from common.admin import BaseAdmin
from .models import MonoBankClient, MonoBankCard, MonoBankStatement
from .forms import MonoBankCardAdminForm
from .services.mono import MonobankService


@admin.register(MonoBankClient)
class MonoBankClientAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "client_token", "status_token"]
    list_display_links = ("id", "name")
    search_fields = ["name", "client_token"]
    readonly_fields = ("id", "created_at", "updated_at")
    save_on_top = True
    save_as = True
    fieldsets = (
        ("Основні дані", {"fields": ("name", "client_token")}),
    ) + BaseAdmin.fieldsets

    @admin.display(description="Статус токену")
    def status_token(self, obj):
        if MonobankService(obj.client_token).is_token_valid():
            return "🟢 Дійсний"
        return "🔴 Недійсний"


@admin.register(MonoBankCard)
class MonoBankCardAdmin(admin.ModelAdmin):
    form = MonoBankCardAdminForm
    list_display = ["client", "card_id", "chat_id", "is_active"]
    list_filter = ["client", "is_active"]
    search_fields = ["client__name", "card_id"]
    actions = ["make_active", "make_inactive"]
    readonly_fields = ("id", "created_at", "updated_at")
    list_editable = ["is_active"]
    save_as = True
    save_on_top = True
    save_as_continue = True
    fieldsets = (
        (
            "Основні дані",
            {"fields": ("client", "card_id", "chat_id", "is_active")},
        ),
    ) + BaseAdmin.fieldsets

    @admin.action(description="✅ Активувати вибрані картки")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="❎ Деактивувати вибрані картки")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    class Media:
        js = ("adminpanel/js/admin.js",)


class CustomAdminLink(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def monobank_statement_link(self):
        url = reverse("bank:monobank_statement")
        return format_html("<a href='{}'>📜 Виписка Monobank</a>", url)

    monobank_statement_link.short_description = "Виписка Monobank"


admin.site.register(MonoBankStatement, CustomAdminLink)
