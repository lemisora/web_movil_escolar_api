from django.db.models import *
from web_movil_escolar_api.serializers import *
from web_movil_escolar_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if user.is_active:
            roles = user.groups.all()
            role_names = [role.name for role in roles]

            profile = None
            profile_data = {}
            if "administrador" in role_names:
                profile = Administradores.objects.filter(user=user).first()
                if profile:
                    profile_data = AdminSerializer(profile).data
            elif "maestro" in role_names:
                profile = Profesores.objects.filter(user=user).first()
                if profile:
                    profile_data = ProfesorSerializer(profile).data

            if not profile:
                return Response(
                    {"message": "Profile not found for this user."}, 404
                )

            token, created = Token.objects.get_or_create(user=user)

            return Response(
                {
                    "id": user.pk,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "token": token.key,
                    "roles": role_names,
                    "profile": profile_data,
                }
            )
        return Response({}, status=status.HTTP_403_FORBIDDEN)


class Logout(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        print("logout")
        user = request.user
        print(str(user))
        if user.is_active:
            token = Token.objects.get(user=user)
            token.delete()

            return Response({"logout": True})

        return Response({"logout": False})
