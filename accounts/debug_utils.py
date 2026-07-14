from django.conf import settings

from .models import ImpostazioniSistema

DEBUG_ENV = getattr(settings, "DEBUG_DA_ENV", settings.DEBUG)


def debug_forzato_db():
    try:
        return ImpostazioniSistema.get_solo().debug_attivo
    except Exception:
        return False


def debug_effettivo():
    return DEBUG_ENV or debug_forzato_db()


def imposta_debug(attivo, utente=None):
    imp = ImpostazioniSistema.get_solo()
    imp.debug_attivo = attivo
    if utente is not None:
        imp.aggiornato_da = utente
    imp.save(update_fields=["debug_attivo", "aggiornato_da", "aggiornato_il"])
    return imp
