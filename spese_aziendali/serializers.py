from rest_framework import serializers

from .models import CategoriaSpesa, RichiestaRimborso


class CategoriaSpesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaSpesa
        fields = ["id", "descrizione"]


class RichiestaRimborsoSerializer(serializers.ModelSerializer):
    dipendente_nome = serializers.CharField(source="dipendente.__str__", read_only=True)
    categoria_descrizione = serializers.CharField(source="categoria.descrizione", read_only=True)
    stato_display = serializers.CharField(source="get_stato_display", read_only=True)

    class Meta:
        model = RichiestaRimborso
        fields = [
            "id", "dipendente", "dipendente_nome",
            "categoria", "categoria_descrizione",
            "data_inserimento", "data_spesa", "importo", "descrizione",
            "riferimento_giustificativo", "stato", "stato_display",
            "responsabile_valutazione", "data_valutazione",
            "motivazione_rifiuto", "data_liquidazione",
        ]
        read_only_fields = [
            "stato", "dipendente", "data_inserimento",
            "responsabile_valutazione", "data_valutazione",
            "motivazione_rifiuto", "data_liquidazione",
        ]
        extra_kwargs = {
            "data_spesa": {"error_messages": {
                "required": "La data della spesa è obbligatoria.",
                "null": "La data della spesa è obbligatoria.",
                "invalid": "Inserisci una data valida.",
            }},
            "categoria": {"error_messages": {
                "required": "La categoria è obbligatoria.",
                "null": "La categoria è obbligatoria.",
                "does_not_exist": "La categoria selezionata non esiste.",
                "incorrect_type": "Categoria non valida.",
            }},
            "importo": {"error_messages": {
                "required": "L'importo è obbligatorio.",
                "null": "L'importo è obbligatorio.",
                "invalid": "Inserisci un importo valido.",
            }},
            "descrizione": {"error_messages": {
                "required": "La descrizione è obbligatoria.",
                "blank": "La descrizione è obbligatoria.",
            }},
        }

    def validate_data_spesa(self, value):
        if not value:
            raise serializers.ValidationError("La data della spesa è obbligatoria.")
        return value

    def validate_categoria(self, value):
        if not CategoriaSpesa.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("La categoria selezionata non esiste.")
        return value

    def validate_importo(self, value):
        if value is None:
            raise serializers.ValidationError("L'importo è obbligatorio.")
        if value <= 0:
            raise serializers.ValidationError("L'importo deve essere maggiore di zero.")
        return value

    def validate_descrizione(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La descrizione è obbligatoria.")
        return value.strip()

    def validate_riferimento_giustificativo(self, value):
        if value and not value.strip():
            raise serializers.ValidationError(
                "Il riferimento giustificativo non può essere composto solo da spazi."
            )
        return value.strip() if value else value
