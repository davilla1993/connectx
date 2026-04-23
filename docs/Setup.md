python manage.py createsuperuser

python manage.py shell -c "from django.contrib.auth import authenticate; user = authenticate(email='carlogbossou93@gmail.com', password='Admin@2026'); print(f'Authentification réussie : {user is not None}');print(f'Compte actif : {user.is_active if user else \"N/A\"}')"

python manage.py changepassword carlogbossou@outlook.fr

