from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from web_movil_escolar_api.views import (
    alumnos,
    auth,
    bootstrap,
    profesores,
    users,
)

from .views.bootstrap import VersionView

# from sistema_escolar_api.views import alumnos
# from sistema_escolar_api.views import maestros

urlpatterns = [
    # Create Admin
    # Endpoints de registro por rol
    path("admin/", users.AdminView.as_view()),
    path("profesor/", profesores.ProfesoresView.as_view()),
    path("alumno/", alumnos.AlumnosView.as_view()),
    
    # Listado de administradores
    path('lista-admins/', users.AdminAll.as_view()),
    # Lista de profesores
    path('lista-profesores/', profesores.ProfesoresAll.as_view()),
    # Lista de alumno
    path('lista-alumnos/', alumnos.AlumnosAll.as_view()),
    
    # Login
    path("login/", auth.CustomAuthToken.as_view()),
    # Logout
    path("logout/", auth.Logout.as_view()),
    # Profile Data
    # path("profile/admin/", users.AdminProfileView.as_view()),
    # path("profile/profesor/", users.ProfesorProfileView.as_view()),
    # path("profile/alumno/", users.AlumnoProfileView.as_view()),
    # Edit Admin
    # path('admins-edit/', users.AdminsViewEdit.as_view())
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
