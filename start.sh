# meditrack-ai/start.sh

#!/bin/bash

echo "🚀 Démarrage de MediTrack AI..."

# Vérifier les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Créer les dossiers
echo "📁 Création des dossiers..."
mkdir -p logs data models

# Vérifier les valeurs de référence
if [ ! -f data/reference_values.json ]; then
    echo "📊 Création des valeurs de référence..."
    echo '{"normal":{"systolic_min":90,"systolic_max":140,"diastolic_min":60,"diastolic_max":90,"label":"Normale"},"elevated":{"systolic_min":140,"systolic_max":160,"diastolic_min":90,"diastolic_max":100,"label":"Élevée"},"hypertension_stage1":{"systolic_min":160,"systolic_max":180,"diastolic_min":100,"diastolic_max":110,"label":"Hypertension stade 1"},"hypertension_stage2":{"systolic_min":180,"systolic_max":250,"diastolic_min":110,"diastolic_max":160,"label":"Hypertension stade 2"},"hypotension":{"systolic_min":0,"systolic_max":90,"diastolic_min":0,"diastolic_max":60,"label":"Hypotension"}}' > data/reference_values.json
fi

# Démarrer l'application
echo "🏃 Démarrage du serveur..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload