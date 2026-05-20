import json
from datetime import datetime
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import AuthorProfile, Book

User = get_user_model()
DEFAULT_PASSWORD = "password123"


class Command(BaseCommand):
    help = "Load authors and books from bookleaf_sample_data.json"

    def handle(self, *args, **options):
        data_path = Path(__file__).resolve().parents[3] / "data" / "bookleaf_sample_data.json"
        with open(data_path, encoding="utf-8") as f:
            payload = json.load(f)

        # Admin user
        admin, created = User.objects.get_or_create(
            email="admin@bookleaf.com",
            defaults={
                "username": "admin",
                "first_name": "BookLeaf",
                "last_name": "Admin",
                "role": User.Role.ADMIN,
                "is_staff": True,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write("Created admin: admin@bookleaf.com / admin123")
        else:
            self.stdout.write("Admin already exists")

        for item in payload["authors"]:
            user, user_created = User.objects.get_or_create(
                email=item["email"],
                defaults={
                    "username": item["author_id"].lower(),
                    "first_name": item["name"].split()[0],
                    "last_name": " ".join(item["name"].split()[1:]),
                    "role": User.Role.AUTHOR,
                },
            )
            if user_created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()

            joined = None
            if item.get("joined_date"):
                joined = datetime.strptime(item["joined_date"], "%Y-%m-%d").date()

            profile, _ = AuthorProfile.objects.update_or_create(
                author_id=item["author_id"],
                defaults={
                    "user": user,
                    "phone": item.get("phone", ""),
                    "city": item.get("city", ""),
                    "joined_date": joined,
                },
            )

            for b in item["books"]:
                pub_date = None
                if b.get("publication_date"):
                    pub_date = datetime.strptime(b["publication_date"], "%Y-%m-%d").date()

                payout_date = None
                if b.get("last_royalty_payout_date"):
                    payout_date = datetime.strptime(b["last_royalty_payout_date"], "%Y-%m-%d").date()

                Book.objects.update_or_create(
                    book_id=b["book_id"],
                    defaults={
                        "author": profile,
                        "title": b["title"],
                        "isbn": b.get("isbn") or "",
                        "genre": b.get("genre") or "",
                        "publication_date": pub_date,
                        "status": b.get("status") or "",
                        "mrp": b.get("mrp"),
                        "author_royalty_per_copy": b.get("author_royalty_per_copy"),
                        "total_copies_sold": b.get("total_copies_sold") or 0,
                        "total_royalty_earned": b.get("total_royalty_earned") or 0,
                        "royalty_paid": b.get("royalty_paid") or 0,
                        "royalty_pending": b.get("royalty_pending") or 0,
                        "last_royalty_payout_date": payout_date,
                        "print_partner": b.get("print_partner"),
                        "available_on": b.get("available_on") or [],
                    },
                )

        self.stdout.write(self.style.SUCCESS("Seed complete. Authors use password: password123"))
