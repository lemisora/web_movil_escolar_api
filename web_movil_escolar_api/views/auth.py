from django.db.models import *
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from web_movil_escolar_api.models import Alumnos, Profesores
from web_movil_escolar_api.serializers import (
    AlumnoSerializer,
    ProfesorSerializer,
    UserSerializer,
)


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if user.is_active:
            # Obtener perfiles y roles de usuario
            roles = user.groups.all()
            # Verificar si el usuario tiene un perfil asociado
            role_names = [role.name for role in roles]

            # Si solo es un rol especifico asignamos el elemento 0
            role_names = role_names[0]

            # Esta función genera la clave dinámica (token) para iniciar sesión
            token, created = Token.objects.get_or_create(user=user)

            # Verificar que tipo de usuario quiere iniciar sesión
            if role_names == "alumno":
                alumno = Alumnos.objects.filter(user=user).first()
                alumno = AlumnoSerializer(alumno).data
                alumno["token"] = token.key
                alumno["rol"] = "alumno"
                return Response(alumno, 200)

            if role_names == "maestro":
                maestro = Profesores.objects.filter(user=user).first()
                maestro = ProfesorSerializer(maestro).data
                maestro["token"] = token.key
                maestro["rol"] = "maestro"
                return Response(maestro, 200)

            if role_names == "administrador":
                user = UserSerializer(user, many=False).data
                user["token"] = token.key
                user["rol"] = "administrador"
                return Response(user, 200)
            else:
                return Response({"details": "Forbidden"}, 403)
                pass

        return Response({}, status=status.HTTP_403_FORBIDDEN)

            # profile = None
            # profile_data = {}
            # if "administrador" in role_names:
            #     profile = Administradores.objects.filter(user=user).first()
            #     if profile:
            #         profile_data = AdminSerializer(profile).data
            # elif "maestro" in role_names:
            #     profile = Profesores.objects.filter(user=user).first()
            #     if profile:
            #         profile_data = ProfesorSerializer(profile).data

            # if not profile:
            #     return Response(
            #         {"message": "Profile not found for this user."}, 404
            #     )

            # token, created = Token.objects.get_or_create(user=user)

            # return Response(
            #     {
            #         "id": user.pk,
            #         "first_name": user.first_name,
            #         "last_name": user.last_name,
            #         "email": user.email,
            #         "token": token.key,
            #         "roles": role_names,
            #         "profile": profile_data,
            #     }
            # )
        return Response({}, status=status.HTTP_403_FORBIDDEN)


class Logout(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        print("logout")
        user = request.user
        print(str(user))
        if user.is_active:
            token = Token.objects.get(user=user)
            token.delete()

            return Response({"logout": True})

        return Response({"logout": False})
