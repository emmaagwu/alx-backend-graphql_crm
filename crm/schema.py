import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from django.utils import timezone

# ==== GraphQL Types ====
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")


# ==== MUTATIONS ====
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            raise Exception("Invalid email format")

        # Check uniqueness
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists")

        # Optional: Validate phone
        if phone and not (
            phone.startswith("+") or phone.replace("-", "").isdigit()
        ):
            raise Exception("Invalid phone format")

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, message="Customer created successfully")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(
            graphene.NonNull(lambda: CustomerInput), required=True
        )

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, customers):
        created = []
        errors = []

        for cust in customers:
            try:
                validate_email(cust.email)
                if Customer.objects.filter(email=cust.email).exists():
                    raise Exception("Email already exists")
                if cust.phone and not (
                    cust.phone.startswith("+") or cust.phone.replace("-", "").isdigit()
                ):
                    raise Exception("Invalid phone format")
                created.append(Customer.objects.create(**cust.__dict__))
            except Exception as e:
                errors.append(f"{cust.email}: {str(e)}")

        return BulkCreateCustomers(customers=created, errors=errors)


class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock):
        if price <= 0:
            raise Exception("Price must be positive")
        if stock < 0:
            raise Exception("Stock cannot be negative")

        product = Product.objects.create(name=name, price=Decimal(price), stock=stock)
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        products = Product.objects.filter(id__in=product_ids)
        if not products:
            raise Exception("No valid products found")
        if len(products) != len(product_ids):
            raise Exception("Some product IDs are invalid")

        total_amount = sum([p.price for p in products])
        order = Order.objects.create(
            customer=customer,
            order_date=order_date or timezone.now(),
            total_amount=total_amount
        )
        order.products.set(products)
        return CreateOrder(order=order)


# ==== ROOT QUERY & MUTATION ====
class Query(graphene.ObjectType):
    pass  # No queries required by spec


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
