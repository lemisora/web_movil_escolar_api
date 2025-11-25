import json

from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import *
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from web_movil_escolar_api.models import (
    Administradores,
    User,
)
from web_movil_escolar_api.serializers import (
    AdminSerializer,
    UserSerializer,
)


class AdminAll(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        admin = Administradores.objects.filter(user__is_active=1).order_by("id")
        lista = AdminSerializer(admin, many=True).data
        return Response(lista, 200)


class AdminView(generics.CreateAPIView):
    # Permisos por método (sobrescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación
        
    # Obtener usuario por ID
    @transaction.atomic
    def get(self, request, *args, **kwargs):
        admin = get_object_or_404(Administradores, id=request.GET.get("id"))
        admin = AdminSerializer(admin, many=False).data
        return Response(admin, 200)

    # Registrar nuevo usuario
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)

        if user.is_valid():
            # Grab user data
            role = request.data["rol"]
            first_name = request.data["first_name"]
            last_name = request.data["last_name"]
            email = request.data["email"]
            password = request.data["password"]
            # Valida si existe el usuario o bien el email registrado
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

            # Cifrar la contraseña
            user.set_password(password)
            user.save()

            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)
            user.save()

            # Almacenar los datos adicionales del administrador
            admin = Administradores.objects.create(
                user=user,
                clave_admin=request.data["clave_admin"],
                telefono=request.data["telefono"],
                rfc=request.data["rfc"].upper(),
                edad=request.data["edad"],
                ocupacion=request.data["ocupacion"],
            )
            admin.save()

            return Response({"admin_created_id": admin.id}, 201)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)

    # Editar/actualizar los datos de un usuario
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        # Se obtiene usuario a actualizar
        admin = get_object_or_404(Administradores, id=request.data["id"])
        admin.clave_admin = request.data["clave_admin"]
        admin.telefono = request.data["telefono"]
        admin.rfc = request.data["rfc"].upper()
        admin.edad = request.data["edad"]
        admin.ocupacion = request.data["ocupacion"]
        admin.save()
        # Actualizar los datos del usuario
        user = admin.user
        user.first_name = request.data["first_name"]
        user.last_name = request.data["last_name"]
        user.save()

        return Response(
            {
                "message": "Administrador actualizado exitosamente",
                "admin": AdminSerializer(admin).data,
            },
            200,
        )
    
    # Eliminar admin con delete (Borrar realmente)
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        admin = get_object_or_404(Administradores, id=request.GET.get("id"))
        try:
            admin.user.delete()
            return Response({"details":"Administrador eliminado"},200)
        except Exception as e:
            return Response({"details":"Algo pasó al eliminar"},400)