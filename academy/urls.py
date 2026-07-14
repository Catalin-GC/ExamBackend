from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AssegnazioneCorsoViewSet,
    CategoriaCorsoViewSet,
    CorsoAcademyViewSet,
    DipendentiListView,
    StatisticheAcademyView,
)

router = DefaultRouter()
router.register(r"corsi", CorsoAcademyViewSet, basename="corsi")
router.register(r"assegnazioni-corsi", AssegnazioneCorsoViewSet, basename="assegnazioni")
router.register(r"categorie-corso", CategoriaCorsoViewSet, basename="categorie-corso")

urlpatterns = [
    path("", include(router.urls)),
    path("dipendenti/", DipendentiListView.as_view(), name="dipendenti"),
    path("statistiche/academy/", StatisticheAcademyView.as_view(), name="statistiche-academy"),
]
