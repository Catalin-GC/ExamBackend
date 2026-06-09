from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CategoriaSpesa, RichiestaRimborso
from .permissions import IsResponsabile
from .serializers import CategoriaSpesaSerializer, RichiestaRimborsoSerializer


class CategoriaSpesaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CategoriaSpesa.objects.all()
    serializer_class = CategoriaSpesaSerializer
    permission_classes = [IsAuthenticated]


class RichiestaRimborsoViewSet(viewsets.ModelViewSet):
    serializer_class = RichiestaRimborsoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = RichiestaRimborso.objects.select_related("dipendente", "categoria")
        if not user.is_responsabile:
            qs = qs.filter(dipendente=user)

        params = self.request.query_params
        if stato := params.get("stato"):
            qs = qs.filter(stato=stato)
        if categoria := params.get("categoria"):
            qs = qs.filter(categoria_id=categoria)
        if mese := params.get("mese"):  # formato YYYY-MM
            anno, m = mese.split("-")
            qs = qs.filter(data_spesa__year=anno, data_spesa__month=m)
        if user.is_responsabile and (dip := params.get("dipendente")):
            qs = qs.filter(dipendente_id=dip)
        return qs

    def perform_create(self, serializer):
        serializer.save(dipendente=self.request.user,
                         stato=RichiestaRimborso.Stato.IN_ATTESA)

    def _check_owner_in_attesa(self, richiesta, azione="modificare"):
        if richiesta.dipendente != self.request.user:
            raise PermissionDenied("Non puoi gestire richieste di altri dipendenti.")
        if richiesta.stato != RichiestaRimborso.Stato.IN_ATTESA:
            raise ValidationError(
                f"Solo le richieste in attesa possono essere {azione}."
            )

    def update(self, request, *args, **kwargs):
        self._check_owner_in_attesa(self.get_object(), "modificate")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._check_owner_in_attesa(self.get_object(), "eliminate")
        return super().destroy(request, *args, **kwargs)

    
    """ Azioni del responsabile """
    @action(detail=True, methods=["put"], permission_classes=[IsResponsabile])

    def approva(self, request, pk=None):
        r = self.get_object()
        if r.stato != RichiestaRimborso.Stato.IN_ATTESA:
            raise ValidationError("Solo le richieste in attesa possono essere approvate.")
        r.stato = RichiestaRimborso.Stato.APPROVATA
        r.responsabile_valutazione = request.user
        r.data_valutazione = timezone.now()
        r.save()
        return Response(self.get_serializer(r).data)

    @action(detail=True, methods=["put"], permission_classes=[IsResponsabile])
    def rifiuta(self, request, pk=None):
        r = self.get_object()
        if r.stato != RichiestaRimborso.Stato.IN_ATTESA:
            raise ValidationError("Solo le richieste in attesa possono essere rifiutate.")
        r.stato = RichiestaRimborso.Stato.RIFIUTATA
        r.responsabile_valutazione = request.user
        r.data_valutazione = timezone.now()
        r.motivazione_rifiuto = request.data.get("motivazione_rifiuto", "")
        r.save()
        return Response(self.get_serializer(r).data)

    @action(detail=True, methods=["put"], permission_classes=[IsResponsabile])
    def liquida(self, request, pk=None):
        r = self.get_object()
        if r.stato != RichiestaRimborso.Stato.APPROVATA:
            raise ValidationError("Si può liquidare solo una richiesta approvata.")
        r.stato = RichiestaRimborso.Stato.LIQUIDATA
        r.data_liquidazione = timezone.now()
        r.save()
        return Response(self.get_serializer(r).data)


class StatisticheRimborsiView(APIView):
    permission_classes = [IsResponsabile]

    def get(self, request):
        qs = RichiestaRimborso.objects.all()
        p = request.query_params
        if mese := p.get("mese"):
            anno, m = mese.split("-")
            qs = qs.filter(data_spesa__year=anno, data_spesa__month=m)
        if cat := p.get("categoriaId"):
            qs = qs.filter(categoria_id=cat)
        if dip := p.get("dipendenteId"):
            qs = qs.filter(dipendente_id=dip)

        dati = (
            qs.annotate(mese=TruncMonth("data_spesa"))
            .values("mese", "categoria__descrizione")
            .annotate(
                numeroRichieste=Count("id"),
                totaleRichiesto=Sum("importo"),
                totaleApprovato=Sum("importo", filter=Q(
                    stato__in=["APPROVATA", "LIQUIDATA"])),
                totaleLiquidato=Sum("importo", filter=Q(stato="LIQUIDATA")),
            )
            .order_by("mese")
        )
        return Response([
            {
                "mese": d["mese"].strftime("%Y-%m") if d["mese"] else None,
                "categoria": d["categoria__descrizione"],
                "numeroRichieste": d["numeroRichieste"],
                "totaleRichiesto": d["totaleRichiesto"] or 0,
                "totaleApprovato": d["totaleApprovato"] or 0,
                "totaleLiquidato": d["totaleLiquidato"] or 0,
            }
            for d in dati
        ])