from django.contrib import admin

from .models import AssegnazioneCorso, CategoriaCorso, CorsoAcademy


@admin.register(CategoriaCorso)
class CategoriaCorsoAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(CorsoAcademy)
class CorsoAcademyAdmin(admin.ModelAdmin):
    list_display = ("titolo", "categoria", "durata_ore", "obbligatorio", "attivo")
    list_filter = ("attivo", "obbligatorio", "categoria")
    search_fields = ("titolo", "descrizione")


@admin.register(AssegnazioneCorso)
class AssegnazioneCorsoAdmin(admin.ModelAdmin):
    list_display = (
        "id", "corso", "dipendente", "data_assegnazione",
        "data_scadenza", "stato", "data_completamento",
    )
    list_filter = ("stato", "corso__categoria")
    search_fields = ("corso__titolo", "dipendente__email", "dipendente__cognome")
    autocomplete_fields = ("corso", "dipendente")
