from django.contrib import admin
from django.urls import include, path

api_urls = [
    path('api/', include('api.urls')),
    path('api/auth/', include('djoser.urls.authtoken'))
]

urlpatterns = [
    path('', include(api_urls)),
    path('admin/', admin.site.urls),
]
