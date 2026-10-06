import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'suncu_config.settings')
django.setup()

from django.contrib.auth.models import User

try:
    user = User.objects.get(username='admin') # Remplace 'admin' par ton pseudo si besoin
    user.set_password('123456789123456789') # Mets ton nouveau mot de passe ici
    user.save()
    print("=== MOT DE PASSE MODIFIE AVEC SUCCES ===")
except User.DoesNotExist:
    print("=== UTILISATEUR INTROUVABLE ===")