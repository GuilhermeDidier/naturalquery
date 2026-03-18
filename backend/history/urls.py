from django.urls import path
from .views import QueryView, HistoryView

urlpatterns = [
    path("query", QueryView.as_view()),
    path("history", HistoryView.as_view()),
]
