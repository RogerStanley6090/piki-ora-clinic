# Piki Ora Medical Centre — Appointment System

A Django 5 web application that lets patients register, browse doctors,
view available time slots, and book/edit/cancel appointments. Clinic
admins use a fully custom dashboard (separate from Django's built-in
admin) to manage doctors, slots, appointments and user accounts.

> **Assignment note:** Per the assignment requirements, the custom dashboard
> at `/dashboard/` is the admin interface; Django's built-in admin
> (`django.contrib.admin`) is intentionally excluded.

---

## Features

- Custom `User` model with a `role` field (`patient` / `admin`).
- Patient self-registration, login, logout, profile.
- Browse doctors and their available time slots.
- Book appointments with database-level double-booking protection
  (`OneToOneField` on `Appointment.slot` + `select_for_update` row locking).
- Patients can edit the reason for an appointment or cancel it (which frees
  the slot back up for someone else).
- Custom admin dashboard at `/dashboard/`:
  - CRUD for doctors, slots, appointments and users.
  - Live overview metrics.
  - Protected by an `@admin_required` decorator.
- Bootstrap 5 UI via CDN with auth-aware navigation.
- WhiteNoise for production static-file serving (no extra web server).
- SQLite locally, Postgres on Vercel via `dj-database-url`.

---

## Project layout

```
piki_ora_clinic/
├── manage.py
├── requirements.txt
├── vercel.json
├── build_files.sh
├── .env.example
├── piki_ora_clinic/    # Django project (settings, urls, wsgi)
├── accounts/           # Custom user, auth, profile
├── clinic/             # Doctors, slots, appointments (patient-facing)
├── dashboard/          # Custom admin dashboard
├── templates/          # All HTML templates
└── static/css/         # Custom styles
```

---

## 1. Run it locally (the quick path)

Requires **Python 3.10+**.

```bash
# 1. Clone or unzip the project, then enter it.
cd piki_ora_clinic

# 2. Create and activate a virtual environment.
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# 3. Install dependencies.
pip install -r requirements.txt

# 4. (Optional) copy the env template — defaults are fine for local dev.
cp .env.example .env

# 5. Apply migrations.
python manage.py makemigrations
python manage.py migrate

# 6. Seed sample data (3 doctors, lots of slots, admin + patient users).
python manage.py seed_data

# 7. Run the dev server.
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

### Pre-seeded test accounts

| Role    | Username | Password           |
|---------|----------|--------------------|
| Admin   | `admin`  | `Admin@PikiOra2026`|
| Patient | `patient`| `Patient@2026`     |

You can also register your own patient at <http://127.0.0.1:8000/accounts/register/>.

---

## 2. Create the first admin user (without seeding)

If you'd rather not run `seed_data`, create an admin manually:

```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
u = U.objects.create_user(
    username='admin',
    email='admin@example.com',
    password='Admin@PikiOra2026',
    first_name='Site', last_name='Admin',
    role='admin',
)
print('Created', u)
"
```

> Tip: `python manage.py createsuperuser` also works and produces a user
> with `role='patient'` by default — open the dashboard's Users page after
> logging in and change the role to `admin` if you go this route.

---

## 3. Re-seed (wipe & repopulate)

```bash
python manage.py seed_data --flush
```

---

## 4. Deploy to Vercel

1. Push the project to a GitHub repo.
2. In Vercel, "Add New Project" -> import the repo. The included
   `vercel.json` and `build_files.sh` configure the Python runtime,
   route everything to `piki_ora_clinic/wsgi.py`, and run
   `collectstatic` at build time.
3. Provision a Postgres database (Vercel Postgres, Neon, Supabase, etc.)
   and copy the connection string.
4. In the Vercel project's **Environment Variables**, set:

   | Key             | Example value                                    |
   |-----------------|--------------------------------------------------|
   | `SECRET_KEY`    | a 50+ char random string                         |
   | `DEBUG`         | `False`                                          |
   | `ALLOWED_HOSTS` | `your-app.vercel.app,.vercel.app`                |
   | `DATABASE_URL`  | `postgres://user:pass@host:5432/dbname`          |

5. Deploy. After the first deploy, run migrations against the Postgres
   database from your local machine:

   ```bash
   DATABASE_URL='postgres://user:pass@host:5432/dbname' \
       python manage.py migrate
   ```

6. (Optional) Seed sample data the same way:

   ```bash
   DATABASE_URL='...' python manage.py seed_data
   ```

---

## URL map

| Path                                   | Purpose                              |
|----------------------------------------|--------------------------------------|
| `/`                                    | Public landing page                  |
| `/accounts/register/`                  | Patient registration                 |
| `/accounts/login/`                     | Login                                |
| `/accounts/logout/`                    | Logout                               |
| `/accounts/profile/`                   | View your profile                    |
| `/clinic/doctors/`                     | Browse doctors                       |
| `/clinic/doctors/<id>/`                | Doctor profile + available slots     |
| `/clinic/book/<slot_id>/`              | Book a slot                          |
| `/clinic/my/`                          | Your appointments                    |
| `/clinic/appointments/<id>/edit/`      | Edit an appointment                  |
| `/clinic/appointments/<id>/cancel/`    | Cancel an appointment                |
| `/dashboard/`                          | Admin overview (admin-only)          |
| `/dashboard/doctors/` etc.             | Admin CRUD pages                     |

---

## How double-booking is prevented

1. **Database**: `Appointment.slot` is a `OneToOneField` — at most one
   appointment row can ever point at a slot.
2. **Constraint**: `AppointmentSlot` has a unique constraint on
   `(doctor, start_time)` so no two slots can collide for the same doctor.
3. **Form**: `BookingForm.clean_slot` rejects past slots, slots flagged as
   unavailable, and slots that already have a confirmed appointment.
4. **View**: the booking is wrapped in a `transaction.atomic` block and
   uses `select_for_update` to row-lock the slot before flipping it to
   `is_available=False`.

---

## Tests / sanity checks

```bash
python manage.py check         # static checks
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Then `curl` a few URLs to confirm 200 responses:

```bash
curl -I http://127.0.0.1:8000/
curl -I http://127.0.0.1:8000/accounts/login/
curl -I http://127.0.0.1:8000/accounts/register/
curl -I http://127.0.0.1:8000/clinic/doctors/
curl -I http://127.0.0.1:8000/dashboard/   # 302 -> /accounts/login/
```
