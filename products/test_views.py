from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Product, Category


User = get_user_model()


class ProductViewTests(APITestCase):

    def setUp(self):
        # Create users with unique email addresses
        self.staff_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="admin123",
            is_staff=True,
        )

        self.customer = User.objects.create_user(
            username="customer",
            email="customer@test.com",
            password="customer123",
        )

        # Create category
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic products",
            is_active=True,
        )

        # Create products
        self.product1 = Product.objects.create(
            category=self.category,
            name="Laptop",
            slug="laptop",
            sku="LAP001",
            description="A laptop",
            price=Decimal("1000.00"),
            stock_quantity=10,
            is_active=True,
        )

        self.product2 = Product.objects.create(
            category=self.category,
            name="Phone",
            slug="phone",
            sku="PHO001",
            description="A smartphone",
            price=Decimal("500.00"),
            stock_quantity=20,
            is_active=True,
        )

        self.product_list_url = "/api/products/"
        self.product_detail_url = f"/api/products/{self.product1.id}/"

    # -------------------------
    # PRODUCT LIST TESTS
    # -------------------------

    def test_get_products(self):
        response = self.client.get(self.product_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_products_returns_paginated_response(self):
        response = self.client.get(self.product_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)

    # -------------------------
    # PRODUCT CREATE TESTS
    # -------------------------

    def test_staff_can_create_product(self):
        self.client.force_authenticate(user=self.staff_user)

        data = {
            "category": self.category.id,
            "name": "Keyboard",
            "slug": "keyboard",
            "sku": "KEY001",
            "description": "Mechanical keyboard",
            "price": "100.00",
            "stock_quantity": 15,
            "is_active": True,
        }

        response = self.client.post(
            self.product_list_url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Product.objects.filter(name="Keyboard").exists()
        )

    def test_anonymous_user_cannot_create_product(self):
        data = {
            "category": self.category.id,
            "name": "Keyboard",
            "slug": "keyboard",
            "sku": "KEY001",
            "description": "Mechanical keyboard",
            "price": "100.00",
            "stock_quantity": 15,
            "is_active": True,
        }

        response = self.client.post(
            self.product_list_url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_customer_cannot_create_product(self):
        self.client.force_authenticate(user=self.customer)

        data = {
            "category": self.category.id,
            "name": "Keyboard",
            "slug": "keyboard",
            "sku": "KEY001",
            "description": "Mechanical keyboard",
            "price": "100.00",
            "stock_quantity": 15,
            "is_active": True,
        }

        response = self.client.post(
            self.product_list_url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # -------------------------
    # PRODUCT DETAIL TESTS
    # -------------------------

    def test_get_product_detail(self):
        response = self.client.get(self.product_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Laptop")

    # -------------------------
    # PRODUCT UPDATE TESTS
    # -------------------------

    def test_staff_can_update_product(self):
        self.client.force_authenticate(user=self.staff_user)

        data = {
            "name": "Updated Laptop",
        }

        response = self.client.patch(
            self.product_detail_url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.product1.refresh_from_db()
        self.assertEqual(self.product1.name, "Updated Laptop")

    def test_customer_cannot_update_product(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(
            self.product_detail_url,
            {"name": "Updated Laptop"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # -------------------------
    # PRODUCT DELETE TESTS
    # -------------------------

    def test_staff_can_delete_product(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.delete(self.product_detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Product.objects.filter(id=self.product1.id).exists()
        )

    def test_customer_cannot_delete_product(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.delete(self.product_detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # -------------------------
    # PRODUCT FILTERING TESTS
    # -------------------------

    def test_filter_products_by_category(self):
        response = self.client.get(
            self.product_list_url,
            {"category": self.category.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["count"], 2)

    def test_filter_products_by_minimum_price(self):
        response = self.client.get(
            self.product_list_url,
            {"price__gte": "600"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_products_by_maximum_price(self):
        response = self.client.get(
            self.product_list_url,
            {"price__lte": "600"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_products_by_active_status(self):
        self.product2.is_active = False
        self.product2.save()

        response = self.client.get(
            self.product_list_url,
            {"is_active": "true"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    # -------------------------
    # PRODUCT SEARCH TESTS
    # -------------------------

    def test_search_products_by_name(self):
        response = self.client.get(
            self.product_list_url,
            {"search": "Laptop"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_search_products_by_description(self):
        response = self.client.get(
            self.product_list_url,
            {"search": "smartphone"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_search_products_by_sku(self):
        response = self.client.get(
            self.product_list_url,
            {"search": "LAP001"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    # -------------------------
    # PRODUCT ORDERING TESTS
    # -------------------------

    def test_order_products_by_price_ascending(self):
        response = self.client.get(
            self.product_list_url,
            {"ordering": "price"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.data["results"][0]["name"],
            "Phone",
        )

    def test_order_products_by_price_descending(self):
        response = self.client.get(
            self.product_list_url,
            {"ordering": "-price"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.data["results"][0]["name"],
            "Laptop",
        )

    def test_default_product_ordering(self):
        response = self.client.get(self.product_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.data["results"][0]["name"],
            "Phone",
        )

    # -------------------------
    # PRODUCT PAGINATION TESTS
    # -------------------------

    def test_product_pagination(self):
        for i in range(12):
            Product.objects.create(
                category=self.category,
                name=f"Product {i}",
                slug=f"product-{i}",
                sku=f"SKU{i}",
                description=f"Description {i}",
                price=Decimal("100.00"),
                stock_quantity=10,
                is_active=True,
            )

        response = self.client.get(self.product_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)

    def test_product_custom_page_size(self):
        for i in range(12):
            Product.objects.create(
                category=self.category,
                name=f"Product {i}",
                slug=f"product-{i}",
                sku=f"SKU{i}",
                description=f"Description {i}",
                price=Decimal("100.00"),
                stock_quantity=10,
                is_active=True,
            )

        response = self.client.get(
            self.product_list_url,
            {"page_size": 5},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)


class CategoryViewTests(APITestCase):

    def setUp(self):
        # Create users with unique email addresses
        self.staff_user = User.objects.create_user(
            username="category_admin",
            email="category_admin@test.com",
            password="admin123",
            is_staff=True,
        )

        self.customer = User.objects.create_user(
            username="category_customer",
            email="category_customer@test.com",
            password="customer123",
        )

        # Create categories
        self.category1 = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic products",
            is_active=True,
        )

        self.category2 = Category.objects.create(
            name="Clothing",
            slug="clothing",
            description="Clothing products",
            is_active=True,
        )

        self.category_list_url = "/api/categories/"
        self.category_detail_url = f"/api/categories/{self.category1.id}/"

    # -------------------------
    # CATEGORY LIST TESTS
    # -------------------------

    def test_get_categories(self):
        response = self.client.get(self.category_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_categories_returns_paginated_response(self):
        response = self.client.get(self.category_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)

    # -------------------------
    # CATEGORY CREATE TESTS
    # -------------------------

    def test_staff_can_create_category(self):
        self.client.force_authenticate(user=self.staff_user)

        data = {
            "name": "Books",
            "slug": "books",
            "description": "Books and novels",
            "is_active": True,
        }

        response = self.client.post(
            self.category_list_url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Category.objects.filter(name="Books").exists()
        )

    def test_anonymous_user_cannot_create_category(self):
        data = {
            "name": "Books",
            "slug": "books",
            "description": "Books and novels",
            "is_active": True,
        }

        response = self.client.post(
            self.category_list_url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_customer_cannot_create_category(self):
        self.client.force_authenticate(user=self.customer)

        data = {
            "name": "Books",
            "slug": "books",
            "description": "Books and novels",
            "is_active": True,
        }

        response = self.client.post(
            self.category_list_url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # -------------------------
    # CATEGORY DETAIL TESTS
    # -------------------------

    def test_get_category_detail(self):
        response = self.client.get(self.category_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Electronics")

    # -------------------------
    # CATEGORY UPDATE TESTS
    # -------------------------

    def test_staff_can_update_category(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.patch(
            self.category_detail_url,
            {"name": "Updated Electronics"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.category1.refresh_from_db()
        self.assertEqual(
            self.category1.name,
            "Updated Electronics",
        )

    def test_customer_cannot_update_category(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(
            self.category_detail_url,
            {"name": "Updated Electronics"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # -------------------------
    # CATEGORY DELETE TESTS
    # -------------------------

    def test_staff_can_delete_category(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.delete(self.category_detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Category.objects.filter(id=self.category1.id).exists()
        )

    def test_customer_cannot_delete_category(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.delete(self.category_detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # -------------------------
    # CATEGORY FILTERING TESTS
    # -------------------------

    def test_filter_categories_by_active_status(self):
        self.category2.is_active = False
        self.category2.save()

        response = self.client.get(
            self.category_list_url,
            {"is_active": "true"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    # -------------------------
    # CATEGORY SEARCH TESTS
    # -------------------------

    def test_search_categories_by_name(self):
        response = self.client.get(
            self.category_list_url,
            {"search": "Electronics"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_search_categories_by_description(self):
        response = self.client.get(
            self.category_list_url,
            {"search": "Clothing products"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    # -------------------------
    # CATEGORY ORDERING TESTS
    # -------------------------

    def test_order_categories_by_name(self):
        response = self.client.get(
            self.category_list_url,
            {"ordering": "name"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.data["results"][0]["name"],
            "Clothing",
        )

    def test_default_category_ordering(self):
        response = self.client.get(self.category_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.data["results"][0]["name"],
            "Clothing",
        )

    # -------------------------
    # CATEGORY PAGINATION TESTS
    # -------------------------

    def test_category_pagination(self):
        for i in range(12):
            Category.objects.create(
                name=f"Category {i}",
                slug=f"category-{i}",
                description=f"Description {i}",
                is_active=True,
            )

        response = self.client.get(self.category_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)

    def test_category_custom_page_size(self):
        for i in range(12):
            Category.objects.create(
                name=f"Category {i}",
                slug=f"category-{i}",
                description=f"Description {i}",
                is_active=True,
            )

        response = self.client.get(
            self.category_list_url,
            {"page_size": 5},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)