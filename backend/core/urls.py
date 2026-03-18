from django.urls import path, include, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path("api/auth/", include("accounts.urls")),
    path("api/", include("history.urls")),
]

# Catch-all: serve React SPA for non-API routes
urlpatterns += [
    re_path(r"^(?!api/).*$", TemplateView.as_view(template_name="index.html")),
]
