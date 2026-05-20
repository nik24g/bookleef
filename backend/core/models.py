from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Login user — either an author or an admin."""

    class Role(models.TextChoices):
        AUTHOR = "author", "Author"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.AUTHOR)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email


class AuthorProfile(models.Model):
    """Extra info for an author (from sample data)."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="author_profile")
    author_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=100, blank=True)
    joined_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} ({self.author_id})"


class Book(models.Model):
    author = models.ForeignKey(AuthorProfile, on_delete=models.CASCADE, related_name="books")
    book_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    isbn = models.CharField(max_length=50, blank=True)
    genre = models.CharField(max_length=100, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=100)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    author_royalty_per_copy = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_copies_sold = models.PositiveIntegerField(default=0)
    total_royalty_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    royalty_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    royalty_pending = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_royalty_payout_date = models.DateField(null=True, blank=True)
    print_partner = models.CharField(max_length=100, blank=True, null=True)
    available_on = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.title


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "Open", "Open"
        IN_PROGRESS = "In Progress", "In Progress"
        RESOLVED = "Resolved", "Resolved"
        CLOSED = "Closed", "Closed"

    class Category(models.TextChoices):
        ROYALTY = "Royalty & Payments", "Royalty & Payments"
        ISBN = "ISBN & Metadata Issues", "ISBN & Metadata Issues"
        PRINTING = "Printing & Quality", "Printing & Quality"
        DISTRIBUTION = "Distribution & Availability", "Distribution & Availability"
        PRODUCTION = "Book Status & Production Updates", "Book Status & Production Updates"
        GENERAL = "General Inquiry", "General Inquiry"

    class Priority(models.TextChoices):
        CRITICAL = "Critical", "Critical"
        HIGH = "High", "High"
        MEDIUM = "Medium", "Medium"
        LOW = "Low", "Low"

    author = models.ForeignKey(AuthorProfile, on_delete=models.CASCADE, related_name="tickets")
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    category = models.CharField(max_length=50, choices=Category.choices, default=Category.GENERAL)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    category_overridden = models.BooleanField(default=False)
    priority_overridden = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets"
    )
    ai_draft_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class TicketMessage(models.Model):
    """Messages visible to the author (admin replies)."""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class InternalNote(models.Model):
    """Notes only admins see — not shown to authors."""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="internal_notes")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
