from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import AuthorProfile, Book, InternalNote, Ticket, TicketMessage

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role"]


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id",
            "book_id",
            "title",
            "isbn",
            "genre",
            "publication_date",
            "status",
            "mrp",
            "author_royalty_per_copy",
            "total_copies_sold",
            "total_royalty_earned",
            "royalty_paid",
            "royalty_pending",
            "last_royalty_payout_date",
            "print_partner",
            "available_on",
        ]


class TicketMessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.EmailField(source="sender.email", read_only=True)

    class Meta:
        model = TicketMessage
        fields = ["id", "body", "sender_email", "created_at"]
        read_only_fields = ["id", "sender_email", "created_at"]


class InternalNoteSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = InternalNote
        fields = ["id", "note", "author_email", "created_at"]
        read_only_fields = ["id", "author_email", "created_at"]


class TicketListSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True, allow_null=True)
    author_name = serializers.SerializerMethodField()
    latest_reply = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "subject",
            "description",
            "status",
            "category",
            "priority",
            "book",
            "book_title",
            "author_name",
            "latest_reply",
            "reply_count",
            "created_at",
            "updated_at",
        ]

    def get_author_name(self, obj):
        user = obj.author.user
        return user.get_full_name() or user.email

    def get_latest_reply(self, obj):
        last = obj.messages.order_by("-created_at").first()
        if not last:
            return None
        return {
            "body": last.body,
            "sender_email": last.sender.email,
            "created_at": last.created_at,
        }

    def get_reply_count(self, obj):
        return obj.messages.count()


class AuthorTicketDetailSerializer(serializers.ModelSerializer):
    """Ticket detail for authors — no internal notes."""

    messages = TicketMessageSerializer(many=True, read_only=True)
    book_title = serializers.CharField(source="book.title", read_only=True, allow_null=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "subject",
            "description",
            "status",
            "category",
            "priority",
            "book",
            "book_title",
            "messages",
            "created_at",
            "updated_at",
        ]


class TicketDetailSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    internal_notes = InternalNoteSerializer(many=True, read_only=True)
    book_title = serializers.CharField(source="book.title", read_only=True, allow_null=True)
    author_email = serializers.EmailField(source="author.user.email", read_only=True)
    author_name = serializers.SerializerMethodField()
    assigned_to_email = serializers.EmailField(source="assigned_to.email", read_only=True, allow_null=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "subject",
            "description",
            "status",
            "category",
            "priority",
            "category_overridden",
            "priority_overridden",
            "book",
            "book_title",
            "author_email",
            "author_name",
            "assigned_to",
            "assigned_to_email",
            "ai_draft_response",
            "messages",
            "internal_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["messages", "internal_notes", "author_email", "author_name"]

    def get_author_name(self, obj):
        user = obj.author.user
        return user.get_full_name() or user.email


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["book", "subject", "description"]

    def validate_subject(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("Subject must be at least 3 characters.")
        return value

    def validate_description(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("Please provide more detail (at least 10 characters).")
        return value

    def validate_book(self, book):
        if book is None:
            return book
        request = self.context["request"]
        profile = request.user.author_profile
        if book.author_id != profile.id:
            raise serializers.ValidationError("You can only select your own books.")
        return book


class AdminTicketUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["status", "category", "priority", "assigned_to"]

    def update(self, instance, validated_data):
        if "category" in validated_data:
            instance.category_overridden = True
        if "priority" in validated_data:
            instance.priority_overridden = True
        return super().update(instance, validated_data)


class ReplySerializer(serializers.Serializer):
    body = serializers.CharField()


class InternalNoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternalNote
        fields = ["note"]
