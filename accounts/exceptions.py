from rest_framework.views import exception_handler

MESSAGGI = {
    "Authentication credentials were not provided.": (
        "Autenticazione richiesta. Effettua il login."
    ),
    "You do not have permission to perform this action.": (
        "Non hai i permessi per eseguire questa operazione."
    ),
    "Not found.": "Risorsa non trovata.",
    "Not Found": "Risorsa non trovata.",
    "Method not allowed.": "Metodo non consentito.",
    "Given token not valid for any token type": (
        "Token non valido o scaduto. Effettua di nuovo il login."
    ),
    "Token is invalid or expired": (
        "Token non valido o scaduto. Effettua di nuovo il login."
    ),
    "User not found": "Utente non trovato.",
    "No active account found with the given credentials": (
        "Credenziali non valide. Verifica email e password."
    ),
    "This field is required.": "Questo campo è obbligatorio.",
    "This field may not be blank.": "Questo campo non può essere vuoto.",
    "Enter a valid email address.": "Inserisci un indirizzo email valido.",
    "Enter a valid date.": "Inserisci una data valida.",
    "A valid number is required.": "Inserisci un numero valido.",
    "Incorrect type. Expected pk value, received str.": (
        "Valore non valido per la categoria selezionata."
    ),
    'Invalid pk "0" - object does not exist.': (
        "La categoria selezionata non esiste."
    ),
    "Object with id=0 does not exist.": "La categoria selezionata non esiste.",
    "Operazione riservata ai referenti Academy.": (
        "Operazione riservata ai referenti Academy."
    ),
}

CAMPI = {
    "email": "Email",
    "codice_fiscale": "Codice fiscale",
    "password": "Password",
    "conferma_password": "Conferma password",
    "nome": "Nome",
    "cognome": "Cognome",
    "ruolo": "Ruolo",
    "descrizione": "Descrizione",
    "categoria": "Categoria",
    "stato": "Stato",
    "titolo": "Titolo",
    "durata_ore": "Durata (ore)",
    "obbligatorio": "Obbligatorio",
    "attivo": "Attivo",
    "corso": "Corso",
    "dipendente": "Dipendente",
    "data_assegnazione": "Data assegnazione",
    "data_scadenza": "Data scadenza",
    "data_completamento": "Data completamento",
    "nome": "Nome",
    "non_field_errors": "Errori",
    "detail": "Errore",
}

CHIAVI_API = frozenset({"detail", "non_field_errors"})


def _traduci_testo(testo):
    if not isinstance(testo, str):
        return testo
    if testo in MESSAGGI:
        return MESSAGGI[testo]
    for eng, ita in MESSAGGI.items():
        if eng in testo:
            return testo.replace(eng, ita)
    if testo.startswith("Ensure this field has no more than"):
        return "Il valore inserito è troppo lungo."
    if testo.startswith("Ensure this field has at least"):
        return "Il valore inserito è troppo corto."
    if "object does not exist" in testo:
        return "Il valore selezionato non esiste."
    return testo


def _traduci_dati(dati):
    if isinstance(dati, list):
        return [_traduci_testo(item) if isinstance(item, str) else _traduci_dati(item) for item in dati]
    if isinstance(dati, dict):
        return {
            (chiave if chiave in CHIAVI_API else CAMPI.get(chiave, chiave)): _traduci_dati(valore)
            for chiave, valore in dati.items()
        }
    if isinstance(dati, str):
        return _traduci_testo(dati)
    return dati


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = _traduci_dati(response.data)
    return response
