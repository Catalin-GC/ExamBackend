from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .debug_utils import imposta_debug
from .models import ImpostazioniSistema
from .permissions import IsSuperuser
from .serializers import (
    DebugImpostazioniSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class DebugImpostazioniView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request):
        imp = ImpostazioniSistema.get_solo()
        return Response(DebugImpostazioniSerializer(imp).data)

    def patch(self, request):
        serializer = DebugImpostazioniSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        imp = imposta_debug(
            serializer.validated_data["debug_attivo"],
            utente=request.user,
        )
        return Response(DebugImpostazioniSerializer(imp).data)
