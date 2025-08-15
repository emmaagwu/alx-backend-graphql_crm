import graphene
from graphene_django import DjangoObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order
import re

# -------------------------
# GraphQL Object Types
# -------------------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"

# -------------------------
# Input Types
# -------------------------
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int(required=False)

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)

# -------------------------
# Mutations
# -------------------------
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        # Email uniqueness
        if Customer.objects.filter(email=input.email).exists():
            raise ValidationError("Email already exists")
        
        # Phone format
        if input.phone and not re.match(r"^\+?\d{1,15}$", input.phone):
            raise ValidationError("Invalid phone format")

        customer = Customer.objects.create(**input)
        return CreateCustomer(customer=customer, message="Customer created successfully!")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        created_customers = []
        errors = []

        with transaction.atomic():
            for idx, cust in enumerate(input):
                try:
                    if Customer.objects.filter(email=cust.email).exists():
                        raise ValidationError(f"Duplicate email: {cust.email}")
                    if cust.phone and not re.match(r"^\+?\d{1,15}$", cust.phone):
                        raise ValidationError(f"Invalid phone format: {cust.phone}")

                    customer = Customer.objects.create(**cust)
                    created_customers.append(customer)

                except ValidationError as e:
                    errors.append(f"Row {idx+1}: {str(e)}")
        
        return BulkCreateCustomers(customers=created_customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        if input.price <= 0:
            raise ValidationError("Price must be positive")
        if input.stock is not None and input.stock < 0:
            raise ValidationError("Stock cannot be negative")

        product = Product.objects.create(**input)
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, input):
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            raise ValidationError("Invalid customer ID")

        products = Product.objects.filter(id__in=input.product_ids)
        if products.count() != len(input.product_ids):
            raise ValidationError("Some product IDs are invalid")
        if not products.exists():
            raise ValidationError("At least one product must be selected")

        total_amount = sum([p.price for p in products])

        order = Order.objects.create(customer=customer, total_amount=total_amount)
        order.products.set(products)
        return CreateOrder(order=order)

# -------------------------
# Main Query
# -------------------------
class Query(graphene.ObjectType):
    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)

    def resolve_all_customers(root, info):
        return Customer.objects.all()

    def resolve_all_products(root, info):
        return Product.objects.all()

    def resolve_all_orders(root, info):
        return Order.objects.all()

# -------------------------
# Mutation Wrapper
# -------------------------
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
