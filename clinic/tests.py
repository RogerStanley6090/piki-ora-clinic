"""Tests for the clinic app — focus on the double-booking guarantee."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from clinic.models import Appointment, AppointmentSlot, Doctor

User = get_user_model()


class DoubleBookingTests(TestCase):
    def setUp(self):
        self.doctor = Doctor.objects.create(name="Test Doc", specialization="GP")
        start = timezone.now() + timedelta(days=1)
        self.slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            start_time=start,
            end_time=start + timedelta(minutes=30),
        )
        self.patient1 = User.objects.create_user(username="p1", password="pw", email="p1@example.com")
        self.patient2 = User.objects.create_user(username="p2", password="pw", email="p2@example.com")

    def test_second_patient_cannot_book_same_slot(self):
        # First booking succeeds.
        Appointment.objects.create(patient=self.patient1, slot=self.slot)
        # Second booking against the same slot must be rejected.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Appointment.objects.create(patient=self.patient2, slot=self.slot)
