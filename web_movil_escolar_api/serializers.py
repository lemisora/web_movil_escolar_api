from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Administradores, Alumnos, Profesores


class UserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email")


class AdminSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Administradores
        fields = "__all__"


class ProfesorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    # Define 'materias' explícitamente como JSONField para manejar la codificación/decodificación
    # entre objetos Python y cadenas JSON en la base de datos.
    # required=False permite que no sea enviado en todas las peticiones (ej. PATCH/PUT)
    # allow_null=True permite que el campo sea nulo en la DB si es necesario.
    materias = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Profesores
        fields = "__all__"


class AlumnoSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Alumnos
        fields = "__all__"
