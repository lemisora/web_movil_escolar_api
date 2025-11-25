import json

from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import *
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from web_movil_escolar_api.models import Profesores, User
from web_movil_escolar_api.serializers import ProfesorSerializer, UserSerializer


class ProfesoresAll(generics.CreateAPIView):
    # Obtener todos los maestros
    # Verifica que el usuario este autenticado
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        maestros = Profesores.objects.filter(user__is_active=1).order_by("id")
        lista = ProfesorSerializer(maestros, many=True).data
        for maestro in lista:
            # Si 'materias' es None (ej. en DB no hay datos), asegurar que sea una lista vacía para la respuesta.
            if maestro.get("materias") is None:
                maestro["materias"] = []
        return Response(lista, 200)


class ProfesoresView(generics.CreateAPIView):
    # Permisos por método (sobrescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación
    
    # Obtener usuario por ID
    # Verificar que el usuario esté autenticado
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        maestro = get_object_or_404(Profesores, id=request.GET.get("id"))
        maestro_data = ProfesorSerializer(maestro, many=False).data
        # Si 'materias' es None (ej. en DB no hay datos), asegurar que sea una lista vacía para la respuesta.
        if maestro_data.get("materias") is None:
            maestro_data["materias"] = []
        return Response(maestro_data, 200)

    # Registrar nuevo usuario maestro
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        if user.is_valid():
            role = request.data["rol"]
            first_name = request.data["first_name"]
            last_name = request.data["last_name"]
            email = request.data["email"]
            password = request.data["password"]
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                return Response(
                    {"message": "Username " + email + ", is already taken"}, 400
                )
            user = User.objects.create(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=1,
            )
            user.save()
            user.set_password(password)
            user.save()

            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)
            user.save()
            # Create a profile for the user
            maestro = Profesores.objects.create(
                user=user,
                clave_maestro=request.data["clave_maestro"],
                birthdate=request.data["birthdate"],
                telefono=request.data["telefono"],
                rfc=request.data["rfc"].upper(),
                cubiculo=request.data["cubiculo"],
                area_inv=request.data["area_inv"],
                materias=request.data["materias"],
            )
            maestro.save()
            return Response({"maestro_created_id": maestro.id}, 201)
        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)

    # Editar/actualizar los datos de un usuario
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        maestro_id = request.data.get("id")
        if not maestro_id:
            return Response(
                {"detail": "ID de maestro es requerido para la actualización."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        maestro_instance = get_object_or_404(Profesores, id=maestro_id)
        user_instance = maestro_instance.user

        # 1. Actualizar datos del usuario (first_name, last_name) si están presentes
        user_update_data = {}
        if "first_name" in request.data:
            user_update_data["first_name"] = request.data["first_name"]
        if "last_name" in request.data:
            user_update_data["last_name"] = request.data["last_name"]

        if user_update_data:  # Solo si hay datos para actualizar el usuario
            user_serializer = UserSerializer(
                user_instance, data=user_update_data, partial=True
            )
            if user_serializer.is_valid():
                user_serializer.save()
            else:
                return Response(
                    user_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

        # 2. Actualizar datos del profesor
        profesor_update_data = {}
        # Iterar sobre los campos esperados del profesor
        profesor_fields = [
            "clave_maestro",
            "birthdate",
            "telefono",
            "cubiculo",
            "area_inv",
            "rfc",
            "materias",
        ]
        for field in profesor_fields:
            if field in request.data:
                if field == "rfc":
                    profesor_update_data[field] = request.data[field].upper()
                else:
                    # JSONField en el serializador manejará la codificación/decodificación para 'materias'
                    # simplemente pasamos el valor de request.data directamente
                    profesor_update_data[field] = request.data[field]

        profesor_serializer = ProfesorSerializer(
            maestro_instance, data=profesor_update_data, partial=True
        )
        if not profesor_serializer.is_valid():
            return Response(
                profesor_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        profesor_serializer.save()

        # El serializador ProfesorSerializer ya se encarga de decodificar 'materias' para la salida
        response_maestro_data = profesor_serializer.data
        # Asegurar que 'materias' sea una lista vacía si es None en la respuesta
        if response_maestro_data.get("materias") is None:
            response_maestro_data["materias"] = []

        return Response(
            {
                "message": "Maestro actualizado exitosamente",
                "maestro": response_maestro_data,
            },
            status=status.HTTP_200_OK,
        )

    # Eliminar maestro con delete (Borrar realmente)
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        maestro = get_object_or_404(Profesores, id=request.GET.get("id"))
        try:
            maestro.user.delete()
            return Response({"details":"Maestro eliminado"},200)
        except Exception as e:
            return Response({"details":"Algo pasó al eliminar"},400)
