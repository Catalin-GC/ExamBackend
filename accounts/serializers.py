from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

CAMPI_UTENTE = {
    "email": {"error_messages": {
        "required": "L'email è obbligatoria.",
        "blank": "L'email è obbligatoria.",
        "invalid": "Inserisci un indirizzo email valido.",
    }},
    "nome": {"error_messages": {
        "required": "Il nome è obbligatorio.",
        "blank": "Il nome è obbligatorio.",
    }},
    "cognome": {"error_messages": {
        "required": "Il cognome è obbligatorio.",
        "blank": "Il cognome è obbligatorio.",
    }},
    "ruolo": {"error_messages": {
        "required": "Il ruolo è obbligatorio.",
        "invalid_choice": "Ruolo non valido.",
    }},
    "password": {"error_messages": {
        "required": "La password è obbligatoria.",
        "blank": "La password è obbligatoria.",
    }},
}


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    conferma_password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        error_messages={
            "required": "La conferma password è obbligatoria.",
            "blank": "La conferma password è obbligatoria.",
        },
    )

    class Meta:
        model = User
        fields = ["id", "nome", "cognome", "email", "ruolo", "password", "conferma_password"]
        extra_kwargs = CAMPI_UTENTE

    def validate_nome(self, value):
        if not value.strip():
            raise serializers.ValidationError("Il nome è obbligatorio.")
        return value.strip()

    def validate_cognome(self, value):
        if not value.strip():
            raise serializers.ValidationError("Il cognome è obbligatorio.")
        return value.strip()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email già registrata.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            messaggi = []
            for msg in e.messages:
                testo = str(msg)
                if "too short" in testo or "troppo corta" in testo.lower():
                    messaggi.append("La password è troppo corta.")
                elif "too common" in testo or "troppo comune" in testo.lower():
                    messaggi.append("La password è troppo comune.")
                elif "entirely numeric" in testo or "numerica" in testo.lower():
                    messaggi.append("La password non può essere composta solo da numeri.")
                elif "too similar" in testo or "simile" in testo.lower():
                    messaggi.append("La password è troppo simile ai tuoi dati personali.")
                else:
                    messaggi.append("La password non rispetta i requisiti di sicurezza.")
            raise serializers.ValidationError(messaggi)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("conferma_password"):
            raise serializers.ValidationError(
                {"conferma_password": "Le password non coincidono."}
            )
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            nome=validated_data["nome"],
            cognome=validated_data["cognome"],
            ruolo=validated_data.get("ruolo", User.Ruolo.DIPENDENTE),
        )


class LoginSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "Credenziali non valide. Verifica email e password.",
    }

    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except serializers.ValidationError:
            raise serializers.ValidationError(
                {"detail": "Credenziali non valide. Verifica email e password."}
            )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "nome", "cognome", "email", "ruolo", "date_joined"]


class DebugImpostazioniSerializer(serializers.Serializer):
    debug_attivo = serializers.BooleanField()

    def to_representation(self, instance):
        from .debug_utils import DEBUG_ENV, debug_effettivo, debug_forzato_db

        return {
            "debug_attivo": instance.debug_attivo,
            "debug_env": DEBUG_ENV,
            "debug_effettivo": debug_effettivo(),
            "aggiornato_il": instance.aggiornato_il,
            "aggiornato_da": (
                UserSerializer(instance.aggiornato_da).data
                if instance.aggiornato_da
                else None
            ),
        }
