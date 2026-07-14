from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import AssegnazioneCorso, CategoriaCorso, CorsoAcademy

User = get_user_model()


class CategoriaCorsoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaCorso
        fields = ["id", "nome"]
        extra_kwargs = {
            "nome": {"error_messages": {
                "required": "Il nome della categoria è obbligatorio.",
                "blank": "Il nome della categoria è obbligatorio.",
                "unique": "Esiste già una categoria con questo nome.",
            }},
        }

    def validate_nome(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Il nome della categoria è obbligatorio.")
        return value.strip()


class DipendenteSerializer(serializers.ModelSerializer):
    nome_completo = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = User
        fields = ["id", "nome", "cognome", "email", "nome_completo"]


class CorsoAcademySerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source="categoria.nome", read_only=True)
    numero_assegnazioni = serializers.IntegerField(
        source="assegnazioni.count", read_only=True
    )

    class Meta:
        model = CorsoAcademy
        fields = [
            "id", "titolo", "descrizione",
            "categoria", "categoria_nome",
            "durata_ore", "obbligatorio", "attivo",
            "data_creazione", "numero_assegnazioni",
        ]
        read_only_fields = ["data_creazione"]
        extra_kwargs = {
            "titolo": {"error_messages": {
                "required": "Il titolo del corso è obbligatorio.",
                "blank": "Il titolo del corso è obbligatorio.",
            }},
            "categoria": {"error_messages": {
                "required": "La categoria è obbligatoria.",
                "null": "La categoria è obbligatoria.",
                "does_not_exist": "La categoria selezionata non esiste.",
                "incorrect_type": "Categoria non valida.",
            }},
            "durata_ore": {"error_messages": {
                "required": "La durata prevista è obbligatoria.",
                "null": "La durata prevista è obbligatoria.",
                "invalid": "Inserisci una durata valida in ore.",
            }},
        }

    def validate_titolo(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Il titolo del corso è obbligatorio.")
        return value.strip()

    def validate_durata_ore(self, value):
        if value is None:
            raise serializers.ValidationError("La durata prevista è obbligatoria.")
        if value <= 0:
            raise serializers.ValidationError("La durata prevista deve essere maggiore di zero.")
        return value


class AssegnazioneCorsoSerializer(serializers.ModelSerializer):
    corso_titolo = serializers.CharField(source="corso.titolo", read_only=True)
    categoria = serializers.IntegerField(source="corso.categoria_id", read_only=True)
    categoria_nome = serializers.CharField(source="corso.categoria.nome", read_only=True)
    durata_ore = serializers.IntegerField(source="corso.durata_ore", read_only=True)
    obbligatorio = serializers.BooleanField(source="corso.obbligatorio", read_only=True)
    dipendente_nome = serializers.SerializerMethodField()
    stato_effettivo = serializers.CharField(read_only=True)
    stato_display = serializers.CharField(source="stato_effettivo_display", read_only=True)

    class Meta:
        model = AssegnazioneCorso
        fields = [
            "id",
            "corso", "corso_titolo",
            "categoria", "categoria_nome", "durata_ore", "obbligatorio",
            "dipendente", "dipendente_nome",
            "data_assegnazione", "data_scadenza",
            "stato", "stato_effettivo", "stato_display",
            "data_completamento", "data_creazione",
        ]
        read_only_fields = ["data_creazione"]
        extra_kwargs = {
            "corso": {"error_messages": {
                "required": "Il corso è obbligatorio.",
                "null": "Il corso è obbligatorio.",
                "does_not_exist": "Il corso selezionato non esiste.",
                "incorrect_type": "Corso non valido.",
            }},
            "dipendente": {"error_messages": {
                "required": "Il dipendente è obbligatorio.",
                "null": "Il dipendente è obbligatorio.",
                "does_not_exist": "Il dipendente selezionato non esiste.",
                "incorrect_type": "Dipendente non valido.",
            }},
            "data_scadenza": {"error_messages": {
                "required": "La data di scadenza è obbligatoria.",
                "null": "La data di scadenza è obbligatoria.",
                "invalid": "Inserisci una data di scadenza valida.",
            }},
            "data_assegnazione": {"error_messages": {
                "invalid": "Inserisci una data di assegnazione valida.",
            }},
        }

    def get_dipendente_nome(self, obj):
        d = obj.dipendente
        return f"{d.nome} {d.cognome}"

    def validate_dipendente(self, value):
        if value.ruolo != User.Ruolo.DIPENDENTE:
            raise serializers.ValidationError(
                "Puoi assegnare corsi solo ai dipendenti."
            )
        return value

    def validate_corso(self, value):
        if not value.attivo:
            if self.instance is None or self.instance.corso_id != value.pk:
                raise serializers.ValidationError("Corso non attivo.")
        return value

    def validate_stato(self, value):
        valori = [s.value for s in AssegnazioneCorso.Stato if s != AssegnazioneCorso.Stato.SCADUTO]
        if value not in valori:
            raise serializers.ValidationError("Stato non valido.")
        return value

    def validate(self, attrs):
        data_assegnazione = attrs.get(
            "data_assegnazione",
            getattr(self.instance, "data_assegnazione", None),
        )
        data_scadenza = attrs.get(
            "data_scadenza",
            getattr(self.instance, "data_scadenza", None),
        )
        stato = attrs.get("stato", getattr(self.instance, "stato", AssegnazioneCorso.Stato.ASSEGNATO))
        data_completamento = attrs.get(
            "data_completamento",
            getattr(self.instance, "data_completamento", None),
        )

        if data_assegnazione and data_scadenza and data_scadenza < data_assegnazione:
            raise serializers.ValidationError(
                {"data_scadenza": "La scadenza non può essere prima dell'assegnazione."}
            )

        if stato == AssegnazioneCorso.Stato.COMPLETATO:
            if data_completamento and data_assegnazione and data_completamento < data_assegnazione:
                raise serializers.ValidationError(
                    {"data_completamento": "Il completamento non può essere prima dell'assegnazione."}
                )
        else:
            attrs["data_completamento"] = None

        return attrs

    def create(self, validated_data):
        validated_data["stato"] = AssegnazioneCorso.Stato.ASSEGNATO
        validated_data["data_completamento"] = None
        return super().create(validated_data)

    def update(self, instance, validated_data):
        stato = validated_data.get("stato", instance.stato)
        if stato == AssegnazioneCorso.Stato.COMPLETATO:
            if not validated_data.get("data_completamento"):
                validated_data["data_completamento"] = instance.data_completamento or date.today()
        return super().update(instance, validated_data)
