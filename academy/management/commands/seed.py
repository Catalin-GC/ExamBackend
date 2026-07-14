from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from academy.models import AssegnazioneCorso, CategoriaCorso, CorsoAcademy
from accounts.models import ImpostazioniSistema

User = get_user_model()

PASSWORD_TEST = "Password123!"


class Command(BaseCommand):
    help = "Popola il database con dati di test."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Creazione dati iniziali Academy...")

        categorie_nomi = ["Sicurezza", "Privacy", "Soft Skills", "Tecnico", "Compliance"]
        categorie = {}
        for nome in categorie_nomi:
            cat, _ = CategoriaCorso.objects.get_or_create(nome=nome)
            categorie[nome] = cat

        referente, created = User.objects.get_or_create(
            email="referente@azienda.it",
            defaults={
                "nome": "Laura",
                "cognome": "Bianchi",
                "ruolo": User.Ruolo.REFERENTE,
            },
        )
        if created:
            referente.set_password(PASSWORD_TEST)
            referente.save()
        if not referente.is_superuser:
            referente.is_superuser = True
            referente.is_staff = True
            referente.save(update_fields=["is_superuser", "is_staff"])

        ImpostazioniSistema.objects.get_or_create(pk=1)

        def crea_dipendente(email, nome, cognome):
            utente, creato = User.objects.get_or_create(
                email=email,
                defaults={"nome": nome, "cognome": cognome, "ruolo": User.Ruolo.DIPENDENTE},
            )
            if creato:
                utente.set_password(PASSWORD_TEST)
                utente.save()
            return utente

        dip1 = crea_dipendente("mario.rossi@azienda.it", "Mario", "Rossi")
        dip2 = crea_dipendente("giulia.verdi@azienda.it", "Giulia", "Verdi")
        dip3 = crea_dipendente("luca.neri@azienda.it", "Luca", "Neri")

        corsi_def = [
            {
                "titolo": "Sicurezza sul lavoro - Formazione generale",
                "descrizione": "Formazione obbligatoria sui rischi generali in azienda.",
                "categoria": categorie["Sicurezza"], "durata_ore": 4,
                "obbligatorio": True, "attivo": True,
            },
            {
                "titolo": "Antincendio - Rischio medio",
                "descrizione": "Procedure di prevenzione ed emergenza incendio.",
                "categoria": categorie["Sicurezza"], "durata_ore": 8,
                "obbligatorio": True, "attivo": True,
            },
            {
                "titolo": "GDPR e protezione dei dati",
                "descrizione": "Principi del regolamento europeo sulla privacy.",
                "categoria": categorie["Privacy"], "durata_ore": 6,
                "obbligatorio": True, "attivo": True,
            },
            {
                "titolo": "Comunicazione efficace",
                "descrizione": "Tecniche di comunicazione e ascolto attivo.",
                "categoria": categorie["Soft Skills"], "durata_ore": 12,
                "obbligatorio": False, "attivo": True,
            },
            {
                "titolo": "Introduzione a Python",
                "descrizione": "Fondamenti di programmazione con Python.",
                "categoria": categorie["Tecnico"], "durata_ore": 20,
                "obbligatorio": False, "attivo": True,
            },
            {
                "titolo": "Codice etico aziendale",
                "descrizione": "Regole di condotta e compliance interna.",
                "categoria": categorie["Compliance"], "durata_ore": 3,
                "obbligatorio": True, "attivo": True,
            },
            {
                "titolo": "Excel avanzato (edizione ritirata)",
                "descrizione": "Corso non più erogato, mantenuto per storico.",
                "categoria": categorie["Tecnico"], "durata_ore": 10,
                "obbligatorio": False, "attivo": False,
            },
        ]
        corsi = {}
        for c in corsi_def:
            corso, _ = CorsoAcademy.objects.get_or_create(
                titolo=c["titolo"], defaults=c
            )
            corsi[c["titolo"]] = corso

        oggi = date.today()

        def assegna(dip, titolo_corso, giorni_da_ass, giorni_scadenza,
                    stato=AssegnazioneCorso.Stato.ASSEGNATO, completato_dopo=None):
            data_ass = oggi - timedelta(days=giorni_da_ass)
            data_scad = data_ass + timedelta(days=giorni_scadenza)
            data_compl = None
            if completato_dopo is not None:
                data_compl = data_ass + timedelta(days=completato_dopo)
            return AssegnazioneCorso(
                corso=corsi[titolo_corso], dipendente=dip,
                data_assegnazione=data_ass, data_scadenza=data_scad,
                stato=stato, data_completamento=data_compl,
            )

        if not AssegnazioneCorso.objects.exists():
            assegnazioni = [
                assegna(dip1, "Sicurezza sul lavoro - Formazione generale", 10, 60),
                assegna(dip1, "GDPR e protezione dei dati", 90, 30,
                        stato=AssegnazioneCorso.Stato.COMPLETATO, completato_dopo=20),
                assegna(dip1, "Codice etico aziendale", 50, 20),
                assegna(dip2, "Antincendio - Rischio medio", 120, 45,
                        stato=AssegnazioneCorso.Stato.COMPLETATO, completato_dopo=30),
                assegna(dip2, "Comunicazione efficace", 15, 90),
                assegna(dip2, "Introduzione a Python", 5, 120,
                        stato=AssegnazioneCorso.Stato.ANNULLATO),
                assegna(dip3, "GDPR e protezione dei dati", 8, 40),
                assegna(dip3, "Sicurezza sul lavoro - Formazione generale", 70, 30),
            ]
            AssegnazioneCorso.objects.bulk_create(assegnazioni)

        self.stdout.write(self.style.SUCCESS("Dati iniziali Academy creati con successo."))
        self.stdout.write("")
        self.stdout.write(f"Credenziali di test (password: {PASSWORD_TEST}):")
        self.stdout.write("  Referente Academy: referente@azienda.it")
        self.stdout.write("  Dipendente 1:      mario.rossi@azienda.it")
        self.stdout.write("  Dipendente 2:      giulia.verdi@azienda.it")
        self.stdout.write("  Dipendente 3:      luca.neri@azienda.it")
