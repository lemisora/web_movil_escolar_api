from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views.bootstrap import VersionView
from web_movil_escolar_api.views import bootstrap
from web_movil_escolar_api.views import users
from web_movil_escolar_api.views import auth
# from sistema_escolar_api.views import alumnos
# from sistema_escolar_api.views import maestros

urlpatterns = [
    # Create Admin
    path("register/", users.UserRegistrationView.as_view()),
    # Admin Data
    path("lista-admins/", users.UserProfileView.as_view()),
    # Edit Admin
    # path('admins-edit/', users.AdminsViewEdit.as_view())
   ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
