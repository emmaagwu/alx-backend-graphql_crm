import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from decimal import Decimal
from django.utils import timezone
from graphql import GraphQLError
from .models import Customer, Product, Order

# ---------------- GraphQL Types ----------------
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

# ---------------- Input Types ----------------
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False, default_value=0)

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)

# ---------------- Mutations ----------------
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        try:
            if Customer.objects.filter(email=input.email).exists():
                raise GraphQLError("Email already exists")
            customer = Customer(
                name=input.name,
                email=input.email,
                phone=input.phone
            )
            customer.full_clean()
            customer.save()
            return CreateCustomer(customer=customer, message="Customer created successfully")
        except ValidationError as e:
            raise GraphQLError(f"Failed to create customer: {str(e)}") from None

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(graphene.NonNull(CustomerInput), required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, input):
        created_customers = []
        errors = []

        with transaction.atomic():
            for data in input:
                try:
                    if Customer.objects.filter(email=data.email).exists():
                        errors.append(f"Email already exists: {data.email}")
                        continue
                    customer = Customer(
                        name=data.name,
                        email=data.email,
                        phone=data.phone
                    )
                    customer.full_clean()
                    customer.save()
                    created_customers.append(customer)
                except ValidationError as e:
                    errors.append(f"{data.email}: {str(e)}")
                except Exception:
                    errors.append(f"{data.email}: Failed to create customer")

        return BulkCreateCustomers(customers=created_customers, errors=errors)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    @staticmethod
    def mutate(root, info, input):
        try:
            if input.price <= 0:
                raise GraphQLError("Price must be positive")
            if input.stock < 0:
                raise GraphQLError("Stock cannot be negative")
            product = Product(
                name=input.name,
                price=input.price,
                stock=input.stock
            )
            product.full_clean()
            product.save()
            return CreateProduct(product=product)
        except ValidationError as e:
            raise GraphQLError(f"Failed to create product: {str(e)}") from None

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    @staticmethod
    def mutate(root, info, input):
        try:
            try:
                customer = Customer.objects.get(pk=input.customer_id)
            except ObjectDoesNotExist:
                raise GraphQLError("Invalid customer ID") from None

            products = Product.objects.filter(pk__in=input.product_ids)
            if not products.exists():
                raise GraphQLError("No valid products found")
            if len(products) != len(input.product_ids):
                raise GraphQLError("Some product IDs are invalid")

            order = Order.objects.create(
                customer=customer,
                order_date=input.order_date or timezone.now(),
                total_amount=sum([p.price for p in products])
            )
            order.products.set(products)
            order.save()
            return CreateOrder(order=order)
        except Exception as e:
            raise GraphQLError(f"Failed to create order: {str(e)}") from None

# ---------------- Root Schema ----------------
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

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
