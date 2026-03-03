# snipsel

Mobile-first PWA notes app.

## Deployment via GitHub Container Registry

A pre-built Docker image is automatically published to the GitHub Container Registry on every push to `main`.

### Quick Start

```bash
docker run -d \
  --name snipsel \
  -p 5000:5000 \
  -v ./data:/app/data \
  -v ./uploads:/app/uploads \
  -e SNIPSEL_SECRET_KEY="your-secure-secret-key" \
  -e SNIPSEL_DOMAIN="yourdomain.com" \
  -e SNIPSEL_FRONTEND_URL="https://yourdomain.com" \
  -e VAPID_PUBLIC_KEY="your_vapid_public_key" \
  -e VAPID_PRIVATE_KEY="your_vapid_private_key" \
  -e VAPID_SUBJECT="mailto:admin@yourdomain.com" \
  ghcr.io/mcfetz/snipsel:latest
```

### docker-compose example

```yaml
services:
  snipsel:
    image: ghcr.io/mcfetz/snipsel:latest
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data        # persistent database
      - ./uploads:/app/uploads  # user-uploaded files
    environment:
      SNIPSEL_SECRET_KEY: "your-secure-secret-key"
      SNIPSEL_DOMAIN: "yourdomain.com"
      SNIPSEL_FRONTEND_URL: "https://yourdomain.com"
      VAPID_PUBLIC_KEY: "your_vapid_public_key"
      VAPID_PRIVATE_KEY: "your_vapid_private_key"
      VAPID_SUBJECT: "mailto:admin@yourdomain.com"
```

### Environment Variables

#### Required

| Variable | Default | Description |
|---|---|---|
| `SNIPSEL_SECRET_KEY` | `dev` | Flask secret key used for session signing. **Use a long random string in production.** |
| `SNIPSEL_DOMAIN` | `localhost` | Domain name of the server (without protocol). Required for Passkey (WebAuthn) authentication. |
| `SNIPSEL_FRONTEND_URL` | `http://localhost:5000` | Full URL the app is reachable at (with protocol). Required for Passkey (WebAuthn) authentication. |

#### Storage

| Variable | Default | Description |
|---|---|---|
| `SNIPSEL_DATABASE_URL` | `sqlite:////app/data/snipsel.db` | SQLAlchemy database URL. The default SQLite path maps to the `/app/data` volume. |
| `SNIPSEL_UPLOAD_DIR` | `/app/uploads` | Directory where uploaded files are stored. Maps to the `/app/uploads` volume. |
| `SNIPSEL_MAX_UPLOAD_BYTES` | `10485760` | Maximum allowed file upload size in bytes (default: 10 MB). |

#### Push Notifications (optional, but required for PWA notifications)

| Variable | Default | Description |
|---|---|---|
| `VAPID_PUBLIC_KEY` | – | VAPID public key for Web Push. Generate with `npx web-push generate-vapid-keys`. |
| `VAPID_PRIVATE_KEY` | – | VAPID private key for Web Push. |
| `VAPID_SUBJECT` | – | Contact URI for the push service, e.g. `mailto:admin@yourdomain.com`. |

#### SMTP / E-Mail (optional, for password reset)

| Variable | Default | Description |
|---|---|---|
| `SNIPSEL_SMTP_HOST` | – | SMTP server hostname. |
| `SNIPSEL_SMTP_PORT` | `587` | SMTP server port. |
| `SNIPSEL_SMTP_USERNAME` | – | SMTP login username. |
| `SNIPSEL_SMTP_PASSWORD` | – | SMTP login password. |
| `SNIPSEL_SMTP_USE_TLS` | `1` | Set to `0` to disable STARTTLS. |
| `SNIPSEL_MAIL_FROM` | – | Sender address used for outgoing emails. |
| `SNIPSEL_PUBLIC_BASE_URL` | – | If set, password-reset emails contain a clickable link instead of a raw token. |

### Volumes

| Container path | Purpose |
|---|---|
| `/app/data` | SQLite database file (`snipsel.db`). Mount a named volume or host directory here to persist your data across container restarts and updates. |
| `/app/uploads` | User-uploaded files (images, attachments). Mount a named volume or host directory here to persist uploads. |

> **Important:** Without persistent mounts on both paths all data is lost when the container is removed or updated.

---

## Deployment (build from source)

```bash
# Build the image
docker build -t snipsel .

# Run the container
docker run -d \
  --name snipsel \
  -p 5000:5000 \
  -v ./data:/app/data \
  -v ./uploads:/app/uploads \
  -e SNIPSEL_SECRET_KEY="your-secure-secret-key" \
  -e SNIPSEL_DOMAIN="yourdomain.com" \
  -e SNIPSEL_FRONTEND_URL="https://yourdomain.com" \
  snipsel
```

---

## Development

### Backend (Flask)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

export SNIPSEL_SECRET_KEY="dev"
export SNIPSEL_DATABASE_URL="sqlite:///snipsel.db"
export SNIPSEL_UPLOAD_DIR="./uploads"

flask --app snipsel_api.app run --debug --port 5000

# database migrations
flask --app snipsel_api.app db upgrade
```

### Frontend (Svelte + Vite)

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api/*` requests to the backend during development.
