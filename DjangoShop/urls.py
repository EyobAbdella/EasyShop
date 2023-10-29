from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import debug_toolbar

admin.site.site_header = "Market Admin"
admin.site.index_title = "Admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("__debug__", include(debug_toolbar.urls)),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
    path("store/", include("store.urls")),
    path("", include("payment.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
