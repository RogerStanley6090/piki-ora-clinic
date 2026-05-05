"""
Management command that seeds the database with sample doctors, slots,
an admin user and a patient user. Useful for fast testing and marking.

Usage:
    python manage.py seed_data
    python manage.py seed_data --flush   # wipe existing seed data first
"""

from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from clinic.models import Appointment, AppointmentSlot, Doctor

User = get_user_model()

SAMPLE_DOCTORS = [
    {
        "name": "Aroha Williams",
        "specialization": "General Practice",
        "email": "aroha.williams@pikiora.example",
        "phone": "+64 9 555 0101",
        "bio": "Aroha has 12 years' experience as a GP and a special interest in family health.",
        "photo_url": "https://placehold.co/300x300?text=Dr.+Aroha",
    },
    {
        "name": "Hemi Tane",
        "specialization": "Cardiology",
        "email": "hemi.tane@pikiora.example",
        "phone": "+64 9 555 0102",
        "bio": "Hemi is a consultant cardiologist with a focus on preventative heart health.",
        "photo_url": "https://placehold.co/300x300?text=Dr.+Hemi",
    },
    {
        "name": "Sophie Chen",
        "specialization": "Paediatrics",
        "email": "sophie.chen@pikiora.example",
        "phone": "+64 9 555 0103",
        "bio": "Sophie cares for newborns through teenagers, with a calm and gentle bedside manner.",
        "photo_url": "https://placehold.co/300x300?text=Dr.+Sophie",
    },
]

# 30-minute slots between these times each weekday.
WORKING_HOURS = (time(9, 0), time(16, 30))
SLOT_LENGTH = timedelta(minutes=30)
DAYS_AHEAD = 14


class Command(BaseCommand):
    help = "Seed sample doctors, slots, an admin user, and a patient user."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing appointments, slots, doctors and seeded users first.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        if options["flush"]:
            self.stdout.write(self.style.WARNING("Flushing existing seed data..."))
            Appointment.objects.all().delete()
            AppointmentSlot.objects.all().delete()
            Doctor.objects.all().delete()
            User.objects.filter(username__in=["admin", "patient"]).delete()

        # ---- Users ---------------------------------------------------------
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "first_name": "Site",
                "last_name": "Admin",
                "email": "admin@pikiora.example",
                "role": User.Roles.ADMIN,
            },
        )
        if created:
            admin.set_password("Admin@PikiOra2026")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / Admin@PikiOra2026"))
        else:
            self.stdout.write("Admin user 'admin' already exists, skipping.")

        patient, created = User.objects.get_or_create(
            username="patient",
            defaults={
                "first_name": "Sample",
                "last_name": "Patient",
                "email": "patient@pikiora.example",
                "role": User.Roles.PATIENT,
                "phone": "+64 21 555 1234",
            },
        )
        if created:
            patient.set_password("Patient@2026")
            patient.save()
            self.stdout.write(self.style.SUCCESS("Created patient user: patient / Patient@2026"))
        else:
            self.stdout.write("Patient user 'patient' already exists, skipping.")

        # ---- Doctors -------------------------------------------------------
        doctors: list[Doctor] = []
        for spec in SAMPLE_DOCTORS:
            doctor, created = Doctor.objects.get_or_create(
                name=spec["name"], defaults=spec
            )
            doctors.append(doctor)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created doctor: {doctor.name}"))
            else:
                self.stdout.write(f"Doctor {doctor.name} already exists, skipping.")

        # ---- Slots ---------------------------------------------------------
        tz = timezone.get_current_timezone()
        today = timezone.localdate()
        created_slots = 0
        for offset in range(DAYS_AHEAD):
            day = today + timedelta(days=offset)
            # Skip weekends.
            if day.weekday() >= 5:
                continue
            for doctor in doctors:
                current = datetime.combine(day, WORKING_HOURS[0], tzinfo=tz)
                end_of_day = datetime.combine(day, WORKING_HOURS[1], tzinfo=tz)
                while current + SLOT_LENGTH <= end_of_day:
                    slot, was_created = AppointmentSlot.objects.get_or_create(
                        doctor=doctor,
                        start_time=current,
                        defaults={
                            "end_time": current + SLOT_LENGTH,
                            "is_available": True,
                        },
                    )
                    if was_created:
                        created_slots += 1
                    current += SLOT_LENGTH

        self.stdout.write(self.style.SUCCESS(f"Created {created_slots} new appointment slots."))
        self.stdout.write(self.style.SUCCESS("Seeding complete."))
