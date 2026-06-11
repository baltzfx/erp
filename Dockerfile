# --- Stage 1: Build & Compile Production Tailwind Assets ---
FROM node:22.14.0-alpine AS asset-builder
WORKDIR /build

# Only copy what Tailwind needs to parse for classes
COPY app/core/static ./app/core/static
COPY app/modules ./app/modules
COPY app/shared_templates ./app/shared_templates

# Install Tailwind CLI and compile the output CSS file
RUN npm install @tailwindcss/cli
RUN npx tailwindcss -i ./app/core/static/css/input.css -o ./app/core/static/dist/output.css --minify

# --- Stage 2: Final Light Runtime ---
FROM python:3.11.11-alpine

# Install essential compilation tools for Python wheels
RUN apk update && apk add --no-cache build-base libffi-dev

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

# Cache pip packages independently to speed up subsequent rebuilds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . .

# Copy ONLY the compiled CSS from Stage 1 (Preline references completely removed)
COPY --from=asset-builder /build/app/core/static/dist/output.css ./app/core/static/dist/output.css

EXPOSE 8000

# FIX: Set the PYTHONPATH explicitly so Uvicorn can find the "app" folder module safely
ENV PYTHONPATH=/workspace

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
