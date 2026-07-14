from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Count, ProtectedError, Q
from django.db.models.functions import TruncMonth
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AssegnazioneCorso, CategoriaCorso, CorsoAcademy
from .permissions import IsReferente
from .serializers import (
    AssegnazioneCorsoSerializer,
    CategoriaCorsoSerializer,
    CorsoAcademySerializer,
    DipendenteSerializer,
)

User = get_user_model()


def e_vero(valore):
    testo = str(valore).lower()
    return testo in ("1", "true", "vero", "si", "sì", "yes")


class CategoriaCorsoViewSet(viewsets.ModelViewSet):
    queryset = CategoriaCorso.objects.all()
    serializer_class = CategoriaCorsoSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsReferente()]

    def destroy(self, request, *args, **kwargs):
        categoria = self.get_object()
        if categoria.corsi.exists():
            raise ValidationError("Non puoi eliminare questa categoria.")
        return super().destroy(request, *args, **kwargs)


class CorsoAcademyViewSet(viewsets.ModelViewSet):
    serializer_class = CorsoAcademySerializer
    permission_classes = [IsReferente]

    def get_queryset(self):
        qs = CorsoAcademy.objects.select_related("categoria")
        params = self.request.query_params

        categoria = params.get("categoria")
        if categoria:
            qs = qs.filter(categoria_id=categoria)

        attivo = params.get("attivo")
        if attivo not in (None, ""):
            qs = qs.filter(attivo=e_vero(attivo))

        testo = params.get("q")
        if testo:
            qs = qs.filter(Q(titolo__icontains=testo) | Q(descrizione__icontains=testo))

        return qs

    def destroy(self, request, *args, **kwargs):
        corso = self.get_object()
        if corso.assegnazioni.exists():
            raise ValidationError(
                "Non puoi eliminare un corso con assegnazioni. Disattivalo."
            )
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError("Non puoi eliminare questo corso.")

    @action(detail=True, methods=["put"])
    def disattiva(self, request, pk=None):
        corso = self.get_object()
        corso.attivo = False
        corso.save(update_fields=["attivo"])
        return Response(self.get_serializer(corso).data)

    @action(detail=True, methods=["put"])
    def attiva(self, request, pk=None):
        corso = self.get_object()
        corso.attivo = True
        corso.save(update_fields=["attivo"])
        return Response(self.get_serializer(corso).data)


class AssegnazioneCorsoViewSet(viewsets.ModelViewSet):
    serializer_class = AssegnazioneCorsoSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "annulla"):
            return [IsReferente()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = AssegnazioneCorso.objects.select_related(
            "corso", "corso__categoria", "dipendente"
        )

        if not user.is_referente:
            qs = qs.filter(dipendente=user)

        params = self.request.query_params

        corso = params.get("corso")
        if corso:
            qs = qs.filter(corso_id=corso)

        categoria = params.get("categoria")
        if categoria:
            qs = qs.filter(corso__categoria_id=categoria)

        dipendente = params.get("dipendente")
        if user.is_referente and dipendente:
            qs = qs.filter(dipendente_id=dipendente)

        stato = params.get("stato")
        if stato:
            oggi = date.today()
            if stato == AssegnazioneCorso.Stato.SCADUTO:
                qs = qs.filter(
                    stato=AssegnazioneCorso.Stato.ASSEGNATO,
                    data_scadenza__lt=oggi,
                )
            elif stato == AssegnazioneCorso.Stato.ASSEGNATO:
                qs = qs.filter(
                    stato=AssegnazioneCorso.Stato.ASSEGNATO,
                    data_scadenza__gte=oggi,
                )
            else:
                qs = qs.filter(stato=stato)

        return qs

    @action(detail=True, methods=["put"])
    def completa(self, request, pk=None):
        assegnazione = self.get_object()
        user = request.user

        if not user.is_referente and assegnazione.dipendente_id != user.id:
            raise PermissionDenied("Non puoi modificare corsi di altri.")

        if assegnazione.stato == AssegnazioneCorso.Stato.COMPLETATO:
            raise ValidationError("Corso già completato.")
        if assegnazione.stato == AssegnazioneCorso.Stato.ANNULLATO:
            raise ValidationError("Assegnazione annullata.")

        assegnazione.stato = AssegnazioneCorso.Stato.COMPLETATO
        assegnazione.data_completamento = date.today()
        assegnazione.save(update_fields=["stato", "data_completamento"])
        return Response(self.get_serializer(assegnazione).data)

    @action(detail=True, methods=["put"])
    def annulla(self, request, pk=None):
        assegnazione = self.get_object()
        if assegnazione.stato == AssegnazioneCorso.Stato.COMPLETATO:
            raise ValidationError("Non puoi annullare un corso completato.")
        assegnazione.stato = AssegnazioneCorso.Stato.ANNULLATO
        assegnazione.save(update_fields=["stato"])
        return Response(self.get_serializer(assegnazione).data)


class DipendentiListView(APIView):
    permission_classes = [IsReferente]

    def get(self, request):
        dipendenti = User.objects.filter(
            ruolo=User.Ruolo.DIPENDENTE
        ).order_by("cognome", "nome")
        return Response(DipendenteSerializer(dipendenti, many=True).data)


class StatisticheAcademyView(APIView):
    permission_classes = [IsReferente]

    def get(self, request):
        qs = AssegnazioneCorso.objects.select_related("corso__categoria")
        p = self.request.query_params

        mese = p.get("mese")
        if mese:
            try:
                anno, num_mese = mese.split("-")
                qs = qs.filter(
                    data_assegnazione__year=int(anno),
                    data_assegnazione__month=int(num_mese),
                )
            except (ValueError, AttributeError):
                raise ValidationError({"mese": "Mese non valido. Usa AAAA-MM."})

        categoria = p.get("categoria")
        if categoria:
            qs = qs.filter(corso__categoria_id=categoria)

        dipendente = p.get("dipendente")
        if dipendente:
            qs = qs.filter(dipendente_id=dipendente)

        dati = (
            qs.annotate(periodo=TruncMonth("data_assegnazione"))
            .values("periodo", "corso__categoria__nome")
            .annotate(
                numeroAssegnazioni=Count("id"),
                numeroCompletamenti=Count(
                    "id", filter=Q(stato=AssegnazioneCorso.Stato.COMPLETATO)
                ),
            )
            .order_by("periodo", "corso__categoria__nome")
        )

        risultato = []
        for riga in dati:
            assegnati = riga["numeroAssegnazioni"] or 0
            completati = riga["numeroCompletamenti"] or 0
            if assegnati > 0:
                percentuale = round((completati / assegnati) * 100, 2)
            else:
                percentuale = 0

            risultato.append({
                "mese": riga["periodo"].strftime("%Y-%m") if riga["periodo"] else None,
                "categoria": riga["corso__categoria__nome"],
                "numeroAssegnazioni": assegnati,
                "numeroCompletamenti": completati,
                "percentualeCompletamento": percentuale,
            })

        return Response(risultato)
