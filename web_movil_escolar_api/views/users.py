from django.db.models import *
from django.db import transaction
from web_movil_escolar_api.serializers import UserSerializer
from web_movil_escolar_api.serializers import *
import json
from web_movil_escolar_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import Group


# Custom Permissions
class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.groups.filter(name="administrador").exists()
        )


class IsMaestroUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and request.user.groups.filter(name="maestro").exists()
        )


class IsAlumnoUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and request.user.groups.filter(name="alumno").exists()
        )


class AdminProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = AdminSerializer

    def get_object(self):
        return Administradores.objects.get(user=self.request.user)


class ProfesorProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsMaestroUser]
    serializer_class = ProfesorSerializer

    def get_object(self):
        return Profesores.objects.get(user=self.request.user)


class AlumnoProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAlumnoUser]
    serializer_class = AlumnoSerializer

    def get_object(self):
        return Alumnos.objects.get(user=self.request.user)


class BaseUserRegistrationView(generics.CreateAPIView):
    # Atributo para ser definido por las subclases
    role = None

    def create_specific_profile(self, user, data):
        """
        Método a ser implementado por las subclases para crear el perfil específico.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def get_response_data(self, profile_instance):
        """
        Método a ser implementado por las subclases para retornar los datos de respuesta.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if self.role is None:
            return Response(
                {"message": "Role not defined for this registration endpoint."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        user_serializer = UserSerializer(data=request.data)

        if user_serializer.is_valid():
            first_name = request.data.get("first_name")
            last_name = request.data.get("last_name")
            email = request.data.get("email")
            password = request.data.get("password")

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

            group, created = Group.objects.get_or_create(name=self.role)
            user.groups.add(group)
            user.save()

            # Llama al método abstracto para crear el perfil específico
            try:
                profile_instance = self.create_specific_profile(
                    user, request.data
                )
                return Response(
                    self.get_response_data(profile_instance),
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                # Si falla la creación del perfil, revertir la creación del usuario
                transaction.set_rollback(True)
                return Response(
                    {"message": f"Error creating profile: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            user_serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class AdminRegistrationView(BaseUserRegistrationView):
    role = "administrador"

    def create_specific_profile(self, user, data):
        admin = Administradores.objects.create(
            user=user,
            clave_admin=data.get("clave_admin"),
            telefono=data.get("telefono"),
            rfc=data.get("rfc", "").upper(),
            edad=data.get("edad"),
            ocupacion=data.get("ocupacion"),
        )
        return admin

    def get_response_data(self, profile_instance):
        return {"admin_created_id": profile_instance.id}


class ProfesorRegistrationView(BaseUserRegistrationView):
    role = "maestro"

    def create_specific_profile(self, user, data):
        materias_data = data.get("materias", [])
        profesor = Profesores.objects.create(
            user=user,
            clave_maestro=data.get("clave_maestro"),
            telefono=data.get("telefono"),
            rfc=data.get("rfc", "").upper(),
            birthdate=data.get("birthdate"),
            cubiculo=data.get("cubiculo"),
            area_inv=data.get("area_inv"),
            materias=json.dumps(materias_data),
        )
        profesor.save()
        return profesor

    def get_response_data(self, profile_instance):
        return {"profesor_created_id": profile_instance.id}


class AlumnoRegistrationView(BaseUserRegistrationView):
    role = "alumno"

    def create_specific_profile(self, user, data):
        alumno = Alumnos.objects.create(
            user=user,
            clave_alumno=data.get("clave_alumno"),
            telefono=data.get("telefono"),
            rfc=data.get("rfc", "").upper(),
            birthdate=data.get("birthdate"),
            edad=data.get("edad"),
            ocupacion=data.get("ocupacion"),
        )
        alumno.save()
        return alumno

    def get_response_data(self, profile_instance):
        return {"alumno_created_id": profile_instance.id}
