# snipsel

Mobile-first PWA notes app.

## Deployment (Docker)

Snipsel provides a multi-stage Dockerfile that bundles the frontend and backend into a single container.

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

*Note: `SNIPSEL_DOMAIN` and `SNIPSEL_FRONTEND_URL` are required for Passkey authentication to work correctly.*

## Development

### Backend (Flask)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

pip install -e .

# optional environment
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

The frontend should call the backend via `/api/*` (proxied in dev).

### Configuration

Backend environment variables:

- `SNIPSEL_SECRET_KEY` (default: `dev`)
- `SNIPSEL_DATABASE_URL` (default: `sqlite:///snipsel.db`)
- `SNIPSEL_UPLOAD_DIR` (default: `./uploads`)
- `SNIPSEL_MAX_UPLOAD_BYTES` (default: `10485760`)
- `SNIPSEL_DOMAIN` (default: `localhost` - required for Passkeys)
- `SNIPSEL_FRONTEND_URL` (default: `http://localhost:5173` - required for Passkeys)

SMTP (optional, password reset):

- `SNIPSEL_SMTP_HOST`
- `SNIPSEL_SMTP_PORT` (default: `587`)
- `SNIPSEL_SMTP_USERNAME`
- `SNIPSEL_SMTP_PASSWORD`
- `SNIPSEL_SMTP_USE_TLS` (default: `1`)
- `SNIPSEL_MAIL_FROM`
- `SNIPSEL_PUBLIC_BASE_URL` (optional; if set, email contains a link instead of raw token)
