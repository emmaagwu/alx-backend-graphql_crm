# seed_db.py
import os
import django
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx-backend-graphql_crm.settings')
django.setup()

from crm.models import Customer, Product, Order

def run():
    print("Clearing existing data...")
    Order.objects.all().delete()
    Customer.objects.all().delete()
    Product.objects.all().delete()

    print("Seeding customers...")
    customers = [
        Customer(name="Alice", email="alice@example.com", phone="+1234567890"),
        Customer(name="Bob", email="bob@example.com", phone="123-456-7890"),
        Customer(name="Carol", email="carol@example.com"),
    ]
    Customer.objects.bulk_create(customers)

    print("Seeding products...")
    products = [
        Product(name="Laptop", price=Decimal("999.99"), stock=10),
        Product(name="Mouse", price=Decimal("25.50"), stock=50),
        Product(name="Keyboard", price=Decimal("45.00"), stock=30),
    ]
    Product.objects.bulk_create(products)

    print("Creating a sample order for Alice with Laptop and Mouse...")
    alice = Customer.objects.get(email="alice@example.com")
    laptop = Product.objects.get(name="Laptop")
    mouse = Product.objects.get(name="Mouse")
    order = Order.objects.create(
        customer=alice,
        order_date=timezone.now(),
        total_amount=laptop.price + mouse.price
    )
    order.products.set([laptop, mouse])

    print("✅ Database seeding completed.")

if __name__ == "__main__":
    run()
