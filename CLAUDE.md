# Claude Code Context

## Project Overview

Multi-tenant AI receptionist platform using Telnyx for telephony and AI voice assistants. Tenants sign up, get provisioned with a phone number and AI assistant, and can configure call handling.

## Tech Stack

- **Backend**: Django 6.0.3 + Django REST Framework
- **Database**: PostgreSQL (Docker)
- **Auth**: JWT (djangorestframework-simplejwt)
- **Telephony/AI**: Telnyx (phone numbers + AI assistants)
- **Billing**: Stripe
- **Tunnel**: Cloudflare Tunnel (for webhooks)

## Project Structure

```
backend/
├── settings.py          # Django settings
├── urls.py              # Root URL config
└── features/            # Feature-based architecture
    ├── tenants/         # Tenant management
    ├── agents/          # AI agents (phone + assistant)
    ├── auth/            # Registration, login (JWT)
    ├── telnyx/          # Telnyx webhooks
    ├── billing/         # Stripe subscriptions
    ├── credits/         # Usage credits
    ├── calls/           # Call logs
    ├── leads/           # Lead capture
    └── calendar/        # Meeting scheduling
```

## Key Commands

```bash
# Docker
docker compose up -d              # Start all services
docker compose logs web -f        # Follow web logs
docker compose exec web bash      # Shell into container

# Django (inside container)
python manage.py migrate          # Run migrations
python manage.py createsuperuser  # Create admin user
python manage.py shell            # Django shell

# Database
docker compose exec db psql -U reception  # PostgreSQL shell
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register/` | Create account + tenant |
| `POST /api/auth/login/` | Get JWT token |
| `POST /api/auth/refresh/` | Refresh JWT |
| `GET /api/auth/me/` | Current user info |
| `GET/PATCH /api/tenants/me/` | Tenant config |
| `GET/POST /api/agents/` | List/create agents |
| `GET/PATCH/DELETE /api/agents/<id>/` | Agent CRUD |
| `POST /api/telnyx/webhook/` | Telnyx events |
| `POST /api/billing/webhook/` | Stripe events |

## Models

### Tenant
- `id`, `name`, `owner` (User FK)
- `status`: active, suspended
- `stripe_customer_id`, `stripe_subscription_id`

### Agent
- `tenant` (FK), `name`
- `telnyx_phone_number`, `telnyx_assistant_id`, `telnyx_connection_id`
- `forward_phone_number`, `timeout_seconds`
- `assistant_name`, `assistant_greeting`, `system_prompt`
- `status`: pending, provisioning, active, suspended, failed

### CallLog
- `tenant`, `agent` (FKs)
- `call_sid`, `from_number`, `to_number`
- `status`, `duration`, `lead` (FK)

### Lead
- `tenant` (FK)
- `name`, `phone_number`, `email`, `notes`, `source`

## Environment Variables

Key variables in `.env`:
- `TELNYX_API_KEY`, `TELNYX_PUBLIC_KEY` - Telnyx credentials
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` - Stripe
- `DATABASE_URL` or `POSTGRES_*` - Database
- `SECRET_KEY` - Django secret
- `BASE_WEBHOOK_URL` - Public URL for webhooks

## Development Notes

- All phone configuration is per-agent, not per-tenant
- Telnyx is the only telephony provider (Twilio/Vapi removed)
- Agents are provisioned asynchronously after creation
- Credits are deducted per call minute
- Webhooks require signature validation in production

## Common Tasks

### Adding a new feature app
1. Create directory under `backend/features/<name>/`
2. Add `models.py`, `views.py`, `serializers.py`, `urls.py`, `admin.py`, `apps.py`
3. Add to `INSTALLED_APPS` in settings.py
4. Add URL route in `backend/urls.py`
5. Create migrations: `python manage.py makemigrations <name>`

### Testing webhooks locally
Use Cloudflare Tunnel or ngrok to expose local server, then configure webhook URLs in Telnyx dashboard.
