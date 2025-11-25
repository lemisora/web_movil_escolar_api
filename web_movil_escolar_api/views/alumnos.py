from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import *
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from web_movil_escolar_api.models import Alumnos, User
from web_movil_escolar_api.serializers import AlumnoSerializer, UserSerializer


class AlumnosAll(generics.CreateAPIView):
    #Verificar si el usuario esta autenticado
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        alumnos = Alumnos.objects.filter(user__is_active = 1).order_by("id")
        lista = AlumnoSerializer(alumnos, many=True).data
        
        return Response(lista, 200)
    
class AlumnosView(generics.CreateAPIView):
    # Permisos por método (sobrescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación
        
    # Obtener usuario por ID
    @transaction.atomic
    def get(self, request, *args, **kwargs):
        alumno = get_object_or_404(Alumnos, id=request.GET.get("id"))
        alumno = AlumnoSerializer(alumno, many=False).data
        return Response(alumno, 200)
    
    
    #Registrar nuevo usuario
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
            user.set_password(password)
            user.save()

            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)
            user.save()

            #Create a profile for the user
            alumno = Alumnos.objects.create(user=user,
                                            clave_alumno= request.data["clave_alumno"],
                                            curp= request.data["curp"],
                                            rfc= request.data["rfc"].upper(),
                                            birthdate= request.data["birthdate"],
                                            edad= request.data["edad"],
                                            telefono= request.data["telefono"],
                                            ocupacion= request.data["ocupacion"])
            alumno.save()

            return Response({"Alumno creado con ID: ": alumno.id }, 201)

    # Editar/actualizar los datos de un usuario
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        # Se obtiene usuario a actualizar
        alumno = get_object_or_404(Alumnos, id=request.data["id"])
        alumno.clave_alumno = request.data["clave_alumno"]
        alumno.telefono = request.data["telefono"]
        alumno.curp = request.data["curp"].upper()
        alumno.rfc = request.data["rfc"].upper()
        alumno.edad = request.data["edad"]
        alumno.ocupacion = request.data["ocupacion"]
        alumno.save()
        # Actualizar los datos del usuario
        user = alumno.user
        user.first_name = request.data["first_name"]
        user.last_name = request.data["last_name"]
        user.save()
    
        return Response(
        {
            "message": "Alumno actualizado exitosamente",
            "alumno": AlumnoSerializer(alumno).data,
        },
        200,
    )
    
    # Eliminar alumno con delete (Borrar realmente)
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        alumno = get_object_or_404(Alumnos, id=request.GET.get("id"))
        try:
            alumno.user.delete()
            return Response({"details":"Alumno eliminado"},200)
        except Exception as e:
            return Response({"details":"Algo pasó al eliminar"},400)