from django.db.models import *
from django.db import transaction
from web_movil_escolar_api.serializers import UserSerializer
from web_movil_escolar_api.serializers import *
from web_movil_escolar_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import Group


class UserProfileView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        profile = None
        profile_data = {}
        if user.groups.filter(name="admin").exists():
            profile = Administradores.objects.filter(user=user).first()
            if profile:
                profile_data = AdminSerializer(profile).data
        elif user.groups.filter(name="maestro").exists():
            profile = Profesores.objects.filter(user=user).first()
            if profile:
                profile_data = ProfesorSerializer(profile).data

        if not profile:
            return Response(
                {"message": "Profile not found for this user."}, 404
            )

        return Response(profile_data)


class UserRegistrationView(generics.CreateAPIView):
    # Registrar nuevo usuario
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Serializamos los datos del administrador para volverlo de nuevo JSON
        user_serializer = UserSerializer(data=request.data)

        if user_serializer.is_valid():
            # Grab user data
            role = request.data.get("rol")
            first_name = request.data.get("first_name")
            last_name = request.data.get("last_name")
            email = request.data.get("email")
            password = request.data.get("password")

            # Valida si existe el usuario o bien el email registrado
            if User.objects.filter(email=email).exists():
                return Response(
                    {"message": f"User with email {email} already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.create(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=1,
            )
            user.set_password(password)

            group, created = Group.objects.get_or_create(name=role)
            user.groups.add(group)
            user.save()

            if role == "admin":
                admin = Administradores.objects.create(
                    user=user,
                    clave_admin=request.data.get("clave_admin"),
                    telefono=request.data.get("telefono"),
                    rfc=request.data.get("rfc", "").upper(),
                    edad=request.data.get("edad"),
                    ocupacion=request.data.get("ocupacion"),
                )
                return Response(
                    {"admin_created_id": admin.id},
                    status=status.HTTP_201_CREATED,
                )

            elif role == "maestro":
                import json

                materias_data = request.data.get("materias", [])
                profesor = Profesores.objects.create(
                    user=user,
                    clave_maestro=request.data.get("clave_maestro"),
                    telefono=request.data.get("telefono"),
                    rfc=request.data.get("rfc", "").upper(),
                    birthdate=request.data.get("birthdate"),
                    cubiculo=request.data.get("cubiculo"),
                    area_inv=request.data.get("area_inv"),
                    materias=json.dumps(materias_data),
                )
                profesor.save()
                return Response(
                    {"profesor_created_id": profesor.id},
                    status=status.HTTP_201_CREATED,
                )

            # In case the role is not 'admin' or 'profesor'
            return Response(
                {"message": "Invalid role specified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            user_serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )
