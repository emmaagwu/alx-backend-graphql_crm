import django
import os
from crm.models import Customer, Product

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_backend_graphql_crm.settings")
django.setup()



def seed():
    customers = [
        {"name": "Alice", "email": "alice@example.com", "phone": "+1234567890"},
        {"name": "Bob", "email": "bob@example.com"},
    ]
    for cust in customers:
        Customer.objects.get_or_create(**cust)

    products = [
        {"name": "Laptop", "price": 999.99, "stock": 10},
        {"name": "Mouse", "price": 19.99, "stock": 50},
    ]
    for prod in products:
        Product.objects.get_or_create(**prod)

    print("Database seeded!")

if __name__ == "__main__":
    seed()
