from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import ImpostazioniSistema
from spese_aziendali.models import CategoriaSpesa, RichiestaRimborso

User = get_user_model()


class Command(BaseCommand):
    help = "Popola il database con dati iniziali realistici per i test."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Creazione dati iniziali...")

        # --- Categorie di spesa ---
        categorie_nomi = ["Trasferta", "Pasti", "Pedaggi", "Parcheggi", "Acquisti minori"]
        categorie = {}
        for nome in categorie_nomi:
            cat, _ = CategoriaSpesa.objects.get_or_create(descrizione=nome)
            categorie[nome] = cat

        # --- Responsabile amministrativo ---
        responsabile, created = User.objects.get_or_create(
            email="responsabile@azienda.it",
            defaults={
                "nome": "Laura",
                "cognome": "Bianchi",
                "ruolo": User.Ruolo.RESPONSABILE,
            },
        )
        if created:
            responsabile.set_password("Password123!")
            responsabile.save()
        if not responsabile.is_superuser:
            responsabile.is_superuser = True
            responsabile.is_staff = True
            responsabile.save(update_fields=["is_superuser", "is_staff"])

        ImpostazioniSistema.objects.get_or_create(pk=1)

        # --- Dipendenti ---
        dip1, c1 = User.objects.get_or_create(
            email="mario.rossi@azienda.it",
            defaults={"nome": "Mario", "cognome": "Rossi", "ruolo": User.Ruolo.DIPENDENTE},
        )
        if c1:
            dip1.set_password("Password123!")
            dip1.save()

        dip2, c2 = User.objects.get_or_create(
            email="giulia.verdi@azienda.it",
            defaults={"nome": "Giulia", "cognome": "Verdi", "ruolo": User.Ruolo.DIPENDENTE},
        )
        if c2:
            dip2.set_password("Password123!")
            dip2.save()

        # --- Richieste di rimborso con stati diversi ---
        oggi = date.today()
        ora = timezone.now()

        richieste = [
            # In attesa
            {
                "dipendente": dip1, "categoria": categorie["Trasferta"],
                "data_spesa": oggi - timedelta(days=5), "importo": "120.50",
                "descrizione": "Treno A/R per riunione cliente a Milano",
                "riferimento_giustificativo": "BIGL-2026-001",
                "stato": RichiestaRimborso.Stato.IN_ATTESA,
            },
            {
                "dipendente": dip1, "categoria": categorie["Pasti"],
                "data_spesa": oggi - timedelta(days=4), "importo": "32.00",
                "descrizione": "Pranzo di lavoro con fornitore",
                "stato": RichiestaRimborso.Stato.IN_ATTESA,
            },
            # Approvata
            {
                "dipendente": dip1, "categoria": categorie["Pedaggi"],
                "data_spesa": oggi - timedelta(days=20), "importo": "18.40",
                "descrizione": "Pedaggio autostradale trasferta Torino",
                "riferimento_giustificativo": "TLP-9981",
                "stato": RichiestaRimborso.Stato.APPROVATA,
                "responsabile_valutazione": responsabile,
                "data_valutazione": ora - timedelta(days=15),
            },
            # Liquidata
            {
                "dipendente": dip2, "categoria": categorie["Parcheggi"],
                "data_spesa": oggi - timedelta(days=40), "importo": "25.00",
                "descrizione": "Parcheggio aeroporto per trasferta",
                "stato": RichiestaRimborso.Stato.LIQUIDATA,
                "responsabile_valutazione": responsabile,
                "data_valutazione": ora - timedelta(days=35),
                "data_liquidazione": ora - timedelta(days=30),
            },
            # Rifiutata
            {
                "dipendente": dip2, "categoria": categorie["Acquisti minori"],
                "data_spesa": oggi - timedelta(days=10), "importo": "210.00",
                "descrizione": "Acquisto accessori non autorizzati",
                "stato": RichiestaRimborso.Stato.RIFIUTATA,
                "responsabile_valutazione": responsabile,
                "data_valutazione": ora - timedelta(days=8),
                "motivazione_rifiuto": "Spesa non autorizzata dalla policy aziendale.",
            },
            # Altra in attesa del secondo dipendente
            {
                "dipendente": dip2, "categoria": categorie["Trasferta"],
                "data_spesa": oggi - timedelta(days=2), "importo": "89.90",
                "descrizione": "Taxi e trasporti durante trasferta Roma",
                "stato": RichiestaRimborso.Stato.IN_ATTESA,
            },
        ]

        if not RichiestaRimborso.objects.exists():
            for r in richieste:
                RichiestaRimborso.objects.create(**r)

        self.stdout.write(self.style.SUCCESS("Dati iniziali creati con successo."))
        self.stdout.write("")
        self.stdout.write("Credenziali di test (password: Password123!):")
        self.stdout.write("  Responsabile: responsabile@azienda.it")
        self.stdout.write("  Dipendente 1: mario.rossi@azienda.it")
        self.stdout.write("  Dipendente 2: giulia.verdi@azienda.it")
