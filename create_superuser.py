import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'markdcommerce.settings')
django.setup()

# Import User model
from django.contrib.auth import get_user_model
User = get_user_model()

# Define superuser credentials
SUPERUSER_USERNAME = 'admin'
SUPERUSER_EMAIL = 'sevco@sevco.com'
SUPERUSER_PASSWORD = '31867878'  # Change this to a secure password!

# Check if superuser exists and create if it doesn't
if not User.objects.filter(username=SUPERUSER_USERNAME).exists():
    print(f"Creating superuser {SUPERUSER_USERNAME}...")
    User.objects.create_superuser(
        username=SUPERUSER_USERNAME,
        email=SUPERUSER_EMAIL,
        password=SUPERUSER_PASSWORD
    )
    print("Superuser created successfully!")
else:
    print(f"Superuser {SUPERUSER_USERNAME} already exists.")