from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", views.MeView.as_view(), name="me"),
    path("books/", views.MyBooksView.as_view(), name="my-books"),
    path("tickets/", views.AuthorTicketListCreateView.as_view(), name="author-tickets"),
    path("tickets/<int:pk>/", views.AuthorTicketDetailView.as_view(), name="author-ticket-detail"),
    path("admin/tickets/", views.AdminTicketListView.as_view(), name="admin-tickets"),
    path("admin/tickets/<int:pk>/", views.AdminTicketDetailView.as_view(), name="admin-ticket-detail"),
    path("admin/tickets/<int:pk>/reply/", views.AdminReplyView.as_view(), name="admin-reply"),
    path("admin/tickets/<int:pk>/notes/", views.AdminInternalNoteView.as_view(), name="admin-note"),
    path("admin/tickets/<int:pk>/assign-me/", views.AdminAssignMeView.as_view(), name="admin-assign"),
    path("admin/tickets/<int:pk>/regenerate-draft/", views.AdminRegenerateDraftView.as_view(), name="admin-draft"),
]
