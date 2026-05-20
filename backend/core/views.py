from django.contrib.auth import get_user_model
from django.db.models import Case, IntegerField, When
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from . import ai_service
from .auth_serializers import EmailTokenObtainPairSerializer
from .models import AuthorProfile, Book, InternalNote, Ticket, TicketMessage
from .permissions import IsAdmin, IsAuthor
from .serializers import (
    AdminTicketUpdateSerializer,
    BookSerializer,
    InternalNoteCreateSerializer,
    InternalNoteSerializer,
    ReplySerializer,
    TicketCreateSerializer,
    AuthorTicketDetailSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
    UserSerializer,
)

User = get_user_model()


class LoginView(TokenObtainPairView):
    """POST email + password → JWT access & refresh tokens."""

    serializer_class = EmailTokenObtainPairSerializer


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class MyBooksView(generics.ListAPIView):
    serializer_class = BookSerializer
    permission_classes = [IsAuthor]

    def get_queryset(self):
        return Book.objects.filter(author=self.request.user.author_profile)


class AuthorTicketListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthor]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TicketCreateSerializer
        return TicketListSerializer

    def get_queryset(self):
        return (
            Ticket.objects.filter(author=self.request.user.author_profile)
            .select_related("book")
            .prefetch_related("messages")
        )

    def perform_create(self, serializer):
        profile = self.request.user.author_profile
        ticket = serializer.save(author=profile)
        category, priority = ai_service.classify_ticket(ticket.subject, ticket.description)
        ticket.category = category
        ticket.priority = priority
        ticket = Ticket.objects.select_related("book", "author__user").get(pk=ticket.pk)
        ticket.ai_draft_response = ai_service.draft_response(ticket)
        ticket.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(TicketListSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)


class AuthorTicketDetailView(generics.RetrieveAPIView):
    serializer_class = AuthorTicketDetailSerializer
    permission_classes = [IsAuthor]

    def get_queryset(self):
        return Ticket.objects.filter(author=self.request.user.author_profile).prefetch_related(
            "messages", "internal_notes"
        )


class AdminTicketListView(generics.ListAPIView):
    serializer_class = TicketListSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = Ticket.objects.select_related("book", "author__user", "assigned_to").prefetch_related(
            "messages"
        )
        status_param = self.request.query_params.get("status")
        category = self.request.query_params.get("category")
        priority = self.request.query_params.get("priority")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if status_param:
            qs = qs.filter(status=status_param)
        if category:
            qs = qs.filter(category=category)
        if priority:
            qs = qs.filter(priority=priority)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        # Urgent first, then oldest waiting (assignment: spot urgent + old unresolved)
        priority_rank = Case(
            When(priority=Ticket.Priority.CRITICAL, then=0),
            When(priority=Ticket.Priority.HIGH, then=1),
            When(priority=Ticket.Priority.MEDIUM, then=2),
            When(priority=Ticket.Priority.LOW, then=3),
            default=4,
            output_field=IntegerField(),
        )
        return qs.annotate(priority_rank=priority_rank).order_by("priority_rank", "created_at")


class AdminTicketDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return Ticket.objects.prefetch_related("messages", "internal_notes").select_related(
            "book", "author__user", "assigned_to"
        )

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return AdminTicketUpdateSerializer
        return TicketDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        ticket = self.get_object()
        if not ticket.ai_draft_response:
            ticket.ai_draft_response = ai_service.draft_response(ticket)
            ticket.save(update_fields=["ai_draft_response"])
        serializer = TicketDetailSerializer(ticket)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        ticket = self.get_object()
        serializer = AdminTicketUpdateSerializer(ticket, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        ticket.refresh_from_db()
        return Response(TicketDetailSerializer(ticket).data)


class AdminReplyView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        ticket = Ticket.objects.filter(pk=pk).first()
        if not ticket:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            body=serializer.validated_data["body"],
        )
        if ticket.status == Ticket.Status.OPEN:
            ticket.status = Ticket.Status.IN_PROGRESS
            ticket.save(update_fields=["status", "updated_at"])

        ticket = Ticket.objects.prefetch_related("messages", "internal_notes").get(pk=ticket.pk)
        return Response(TicketDetailSerializer(ticket).data)


class AdminInternalNoteView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        ticket = Ticket.objects.filter(pk=pk).first()
        if not ticket:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = InternalNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = InternalNote.objects.create(
            ticket=ticket,
            author=request.user,
            note=serializer.validated_data["note"],
        )
        return Response(InternalNoteSerializer(note).data, status=status.HTTP_201_CREATED)


class AdminAssignMeView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        ticket = Ticket.objects.filter(pk=pk).first()
        if not ticket:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        ticket.assigned_to = request.user
        ticket.save(update_fields=["assigned_to", "updated_at"])
        return Response(TicketDetailSerializer(ticket).data)


class AdminRegenerateDraftView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        ticket = Ticket.objects.filter(pk=pk).select_related("book", "author__user").first()
        if not ticket:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        ticket.ai_draft_response = ai_service.draft_response(ticket)
        ticket.save(update_fields=["ai_draft_response"])
        return Response({"ai_draft_response": ticket.ai_draft_response})
