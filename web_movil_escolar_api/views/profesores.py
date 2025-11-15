import json

from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import *
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from web_movil_escolar_api.models import Profesores, User
from web_movil_escolar_api.serializers import ProfesorSerializer, UserSerializer


class ProfesoresAll(generics.CreateAPIView):
    #Obtener todos los maestros
    # Verifica que el usuario este autenticado
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        maestros = Profesores.objects.filter(user__is_active=1).order_by("id")
        lista = ProfesorSerializer(maestros, many=True).data
        for maestro in lista:
            if isinstance(maestro, dict) and "materias" in maestro:
                try:
                    maestro["materias"] = json.loads(maestro["materias"])
                except Exception:
                    maestro["materias"] = []
        return Response(lista, 200)
    
class ProfesoresView(generics.CreateAPIView):
    #Registrar nuevo usuario maestro
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        if user.is_valid():
            role = request.data['rol']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            password = request.data['password']
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                return Response({"message":"Username "+email+", is already taken"},400)
            user = User.objects.create( username = email,
                                        email = email,
                                        first_name = first_name,
                                        last_name = last_name,
                                        is_active = 1)
            user.save()
            user.set_password(password)
            user.save()
            
            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)
            user.save()
            #Create a profile for the user
            maestro = Profesores.objects.create(user=user,
                                            clave_maestro= request.data["clave_maestro"],
                                            birthdate= request.data["birthdate"],
                                            telefono= request.data["telefono"],
                                            rfc= request.data["rfc"].upper(),
                                            cubiculo= request.data["cubiculo"],
                                            area_inv= request.data["area_inv"],
                                            materias = json.dumps(request.data["materias"]))
            maestro.save()
            return Response({"maestro_created_id": maestro.id }, 201)
        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)