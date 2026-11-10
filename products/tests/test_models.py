from decimal import Decimal

from django.test import TestCase
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from products.models import Category, Product


class CategoryModelTest(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic devices"
        )

    def test_category_creation(self):
        self.assertIsNotNone(self.category.id)
        self.assertEqual(self.category.name, "Electronics")

    def test_category_string_representation(self):
        self.assertEqual(str(self.category), "Electronics")

    def test_category_default_active_status(self):
        self.assertTrue(self.category.is_active)

    def test_category_name_is_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(
                    name="Electronics",
                    slug="electronics-2"
                )

    def test_category_slug_is_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(
                    name="Computers",
                    slug="electronics"
                )


class ProductModelTest(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Laptop",
            slug="laptop",
            description="Gaming laptop",
            sku="LAP-001",
            price=Decimal("999.99"),
            stock_quantity=10
        )

    def test_product_creation(self):
        self.assertIsNotNone(self.product.id)
        self.assertEqual(self.product.name, "Laptop")

    def test_product_string_representation(self):
        self.assertEqual(str(self.product), "Laptop")

    def test_product_sku_is_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Product.objects.create(
                    category=self.category,
                    name="Another Laptop",
                    slug="another-laptop",
                    sku="LAP-001",
                    price=Decimal("1200.00")
                )

    def test_product_slug_is_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Product.objects.create(
                    category=self.category,
                    name="Another Product",
                    slug="laptop",
                    sku="LAP-002",
                    price=Decimal("500.00")
                )

    def test_product_category_relationship(self):
        self.assertEqual(self.product.category, self.category)
        self.assertIn(self.product, self.category.products.all())

    def test_product_default_stock_quantity(self):
        self.assertEqual(self.product.stock_quantity, 10)

        another_product = Product.objects.create(
            category=self.category,
            name="Mouse",
            slug="mouse",
            sku="MOUSE-001",
            price=Decimal("25.00")
        )

        self.assertEqual(another_product.stock_quantity, 0)

    def test_product_default_active_status(self):
        self.assertTrue(self.product.is_active)

    def test_category_protection(self):
        with self.assertRaises(ProtectedError):
            self.category.delete()