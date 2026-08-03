# meditrack-ai/Dockerfile

# ============================================
# 1. ÉTAPE DE BUILD
# ============================================

FROM python:3.11-slim AS builder

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Définir le dossier de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# 2. ÉTAPE FINALE
# ============================================

FROM python:3.11-slim

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r meditrack && useradd -r -g meditrack meditrack

# Définir le dossier de travail
WORKDIR /app

# Copier les dépendances depuis l'étape de build
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copier le code de l'application
COPY . .

# Créer les dossiers nécessaires
RUN mkdir -p /app/logs /app/data /app/models && \
    chown -R meditrack:meditrack /app

# Changer l'utilisateur
USER meditrack

# Exposer le port
EXPOSE 8000

# Vérification de santé
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]