import json

from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import *
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
        admin = Administradores.objects.filter(user__is_active = 1).order_by("id")
        lista = AdminSerializer(admin, many=True).data
        return Response(lista, 200)

class AdminView(generics.CreateAPIView):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        
        if user.is_valid():
            #Grab user data
            role = request.data['rol']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            password = request.data['password']
            #Valida si existe el usuario o bien el email registrado
            existing_user = User.objects.filter(email=email).first()

            if existing_user:
                return Response({"message":"Username "+email+", is already taken"},400)

            user = User.objects.create( username = email,
                                                email = email,
                                                first_name = first_name,
                                                last_name = last_name,
                                                is_active = 1)

            user.save()
            
            #Cifrar la contraseña
            user.set_password(password)
            user.save()

            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)
            user.save()

            #Almacenar los datos adicionales del administrador
            admin = Administradores.objects.create(user=user,
                                                    clave_admin= request.data["clave_admin"],
                                                    telefono= request.data["telefono"],
                                                    rfc= request.data["rfc"].upper(),
                                                    edad= request.data["edad"],
                                                    ocupacion= request.data["ocupacion"])
            admin.save()

            return Response({"admin_created_id": admin.id }, 201)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)