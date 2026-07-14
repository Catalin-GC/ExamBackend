from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import ImpostazioniSistema, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "nome", "cognome", "ruolo", "is_staff", "is_active", "date_joined")
    list_filter = ("ruolo", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "nome", "cognome")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Anagrafica", {"fields": ("nome", "cognome", "ruolo")}),
        ("Permessi", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Date importanti", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nome", "cognome", "ruolo", "password1", "password2"),
            },
        ),
    )


@admin.register(ImpostazioniSistema)
class ImpostazioniSistemaAdmin(admin.ModelAdmin):
    list_display = ("debug_attivo", "aggiornato_il", "aggiornato_da")
    readonly_fields = ("aggiornato_il", "aggiornato_da")

    def has_add_permission(self, request):
        return not ImpostazioniSistema.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.aggiornato_da = request.user
        super().save_model(request, obj, form, change)
