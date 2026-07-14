from django.core.management.base import BaseCommand, CommandError

from accounts.debug_utils import debug_effettivo, imposta_debug


class Command(BaseCommand):
    help = "Attiva/disattiva il debug globale (salvato nel database)."

    def add_arguments(self, parser):
        parser.add_argument(
            "azione",
            choices=["on", "off", "status"],
            help="on = attiva debug, off = disattiva, status = mostra stato",
        )

    def handle(self, *args, **options):
        azione = options["azione"]

        if azione == "status":
            from accounts.debug_utils import DEBUG_ENV, debug_forzato_db

            self.stdout.write(f"DEBUG env: {DEBUG_ENV}")
            self.stdout.write(f"DEBUG database: {debug_forzato_db()}")
            self.stdout.write(f"DEBUG effettivo: {debug_effettivo()}")
            return

        attivo = azione == "on"
        imposta_debug(attivo)
        stato = "attivato" if attivo else "disattivato"
        self.stdout.write(self.style.SUCCESS(f"Debug {stato}."))
        self.stdout.write(f"DEBUG effettivo: {debug_effettivo()}")

        if attivo:
            self.stdout.write(
                self.style.WARNING(
                    "Attenzione: in produzione le pagine di errore mostreranno dettagli sensibili. "
                    "Disattiva con: python manage.py debug off"
                )
            )
