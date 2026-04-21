#!/bin/bash
set -e

echo "Gestion des permissions pour les médias..."
mkdir -p /app/media
chmod -R 777 /app/media

echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "Migration de la base de données..."
python manage.py migrate --noinput

echo "Démarrage du serveur Daphne..."
exec daphne -b 0.0.0.0 -p 8000 connectx.asgi:application
