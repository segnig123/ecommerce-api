from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Product


# ==================================================
# HELPERS
# ==================================================

def get_results(response):
    """Return the list of items whether or not pagination is enabled."""

    if isinstance(response.data, dict) and "results" in response.data:
        return response.data["results"]

    return response.data


def authenticate(test_case):
    """Create a superuser and authenticate the test client with it."""

    User = get_user_model()

    user = User.objects.create_superuser(
        username="testadmin",
        email="testadmin@example.com",
        password="testpass123"
    )

    test_case.client.force_authenticate(user=user)

    return user


# ==================================================
# PRODUCT API VIEW TESTS
# ==================================================

class ProductAPITests(APITestCase):

    def setUp(self):
        """Authenticate and create a category for product API tests."""

        self.user = authenticate(self)

        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic products",
            is_active=True
        )

        # Payload for the API (the category is sent as an ID)
        self.product_data = {
            "category": self.category.id,
            "name": "Gaming Laptop",
            "slug": "gaming-laptop",
            "description": "High-performance gaming laptop",
            "sku": "LAP-001",
            "price": "1500.00",
            "stock_quantity": 10,
            "is_active": True
        }

        # Data for Product.objects.create() (no "category" key, because the
        # category instance is passed separately in each test)
        self.product_model_data = {
            key: value
            for key, value in self.product_data.items()
            if key != "category"
        }

        self.list_url = reverse("product-list")

    # ----------------------------------------------
    # LIST PRODUCTS
    # ----------------------------------------------

    def test_get_all_products(self):
        """Test retrieving all products."""

        Product.objects.create(
            **self.product_model_data,
            category=self.category
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(get_results(response)), 1)

    def test_get_empty_product_list(self):
        """Test retrieving products when none exist."""

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(get_results(response)), 0)

    def test_product_response_structure(self):
        """Test that product responses contain expected fields."""

        Product.objects.create(
            **self.product_model_data,
            category=self.category
        )

        response = self.client.get(self.list_url)

        product = get_results(response)[0]

        expected_fields = [
            "id",
            "category",
            "name",
            "slug",
            "description",
            "sku",
            "price",
            "stock_quantity",
            "is_active",
            "created_at",
            "updated_at"
        ]

        for field in expected_fields:
            self.assertIn(field, product)

    def test_product_category_relationship(self):
        """Test that products return the correct category ID."""

        Product.objects.create(
            **self.product_model_data,
            category=self.category
        )

        response = self.client.get(self.list_url)

        self.assertEqual(
            get_results(response)[0]["category"],
            self.category.id
        )

    # ----------------------------------------------
    # CREATE PRODUCT
    # ----------------------------------------------

    def test_create_product(self):
        """Test creating a product with valid data."""

        response = self.client.post(
            self.list_url,
            self.product_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Product.objects.count(), 1)

        self.assertEqual(
            Product.objects.get().name,
            "Gaming Laptop"
        )

    def test_create_product_with_invalid_data(self):
        """Test that invalid product data is rejected."""

        invalid_data = {
            "name": "Gaming Laptop"
        }

        response = self.client.post(
            self.list_url,
            invalid_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_with_zero_price(self):
        """Test that zero price is rejected."""

        data = self.product_data.copy()
        data["price"] = "0.00"

        response = self.client.post(
            self.list_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("price", response.data)

    def test_create_product_with_negative_price(self):
        """Test that negative price is rejected."""

        data = self.product_data.copy()
        data["price"] = "-100.00"

        response = self.client.post(
            self.list_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("price", response.data)

    def test_create_product_with_invalid_category(self):
        """Test that nonexistent category IDs are rejected."""

        data = self.product_data.copy()
        data["category"] = 999999

        response = self.client.post(
            self.list_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("category", response.data)

    def test_create_product_with_duplicate_sku(self):
        """Test that duplicate SKUs are rejected."""

        Product.objects.create(
            **self.product_model_data,
            category=self.category
        )

        data = self.product_data.copy()
        data["slug"] = "another-laptop"

        response = self.client.post(
            self.list_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("sku", response.data)

    def test_create_product_with_duplicate_slug(self):
        """Test that duplicate slugs are rejected."""

        Product.objects.create(
            **self.product_model_data,
            category=self.category
        )

        data = self.product_data.copy()
        data["sku"] = "LAP-002"

        response = self.client.post(
            self.list_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("slug", response.data)

    # ----------------------------------------------
    # RETRIEVE PRODUCT
    # ----------------------------------------------

    def test_get_single_product(self):
        """Test retrieving an existing product."""

        product = Product.objects.create(
            **self.product_model_data,
            category=self.category
        )

        detail_url = reverse(
            "product-detail",
            kwargs={"pk": product.pk}
        )

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["name"], "Gaming Laptop")

    def test_get_nonexistent_product(self):
        """Test retrieving a product that does not exist."""

        detail_url = reverse(
            "product-detail",
            kwargs={"pk": 999999}
        )

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------
    # UPDATE PRODUCT
    # ----------------------------------------------

    def test_update_product(self):
        """Test completely updating a product using PUT."""

        product = Product.objects.create(
            **self.product_model_data,
            category=self.category
        )

        updated_data = {
            **self.product_data,
            "name": "Updated Laptop",
            "slug": "updated-laptop",
            "sku": "LAP-002",
            "price": "2000.00"
        }

        detail_url = reverse(
            "product-detail",
            kwargs={"pk": product.pk}
        )

        response = self.client.put(
            detail_url,
            updated_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        product.refresh_from_db()

        self.assertEqual(product.name, "Updated Laptop")
        self.assertEqual(product.price, Decimal("2000.00"))

    def test_partial_update_product(self):
        """Test updating only selected product fields using PATCH."""

        product = Product.objects.create(
            **self.product_model_data,
            category=self.category
        )

        detail_url = reverse(
            "product-detail",
            kwargs={"pk": product.pk}
        )

        response = self.client.patch(
            detail_url,
            {"price": "1800.00"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        product.refresh_from_db()

        self.assertEqual(product.price, Decimal("1800.00"))

        self.assertEqual(product.name, "Gaming Laptop")

    def test_update_product_with_invalid_data(self):
        """Test that invalid product updates are rejected."""

        product = Product.objects.create(
            **self.product_model_data,
            category=self.category
        )

        detail_url = reverse(
            "product-detail",
            kwargs={"pk": product.pk}
        )

        response = self.client.patch(
            detail_url,
            {"price": "-500.00"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        product.refresh_from_db()

        self.assertEqual(product.price, Decimal("1500.00"))

    def test_update_product_category(self):
        """Test assigning a product to another category."""

        product = Product.objects.create(
            **self.product_model_data,
            category=self.category
        )

        another_category = Category.objects.create(
            name="Computers",
            slug="computers",
            is_active=True
        )

        detail_url = reverse(
            "product-detail",
            kwargs={"pk": product.pk}
        )

        response = self.client.patch(
            detail_url,
            {"category": another_category.id},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        product.refresh_from_db()

        self.assertEqual(product.category, another_category)

    def test_update_nonexistent_product(self):
        """Test updating a product that does not exist."""

        detail_url = reverse(
            "product-detail",
            kwargs={"pk": 999999}
        )

        response = self.client.patch(
            detail_url,
            {"price": "2000.00"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------
    # DELETE PRODUCT
    # ----------------------------------------------

    def test_delete_product(self):
        """Test deleting an existing product."""

        product = Product.objects.create(
            **self.product_model_data,
            category=self.category
        )

        detail_url = reverse(
            "product-detail",
            kwargs={"pk": product.pk}
        )

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(
            Product.objects.filter(pk=product.pk).exists()
        )

    def test_delete_nonexistent_product(self):
        """Test deleting a product that does not exist."""

        detail_url = reverse(
            "product-detail",
            kwargs={"pk": 999999}
        )

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ==================================================
# CATEGORY API VIEW TESTS
# ==================================================

class CategoryAPITests(APITestCase):

    def setUp(self):

        self.user = authenticate(self)

        self.category_data = {
            "name": "Electronics",
            "slug": "electronics",
            "description": "Electronic products",
            "is_active": True
        }

        self.list_url = reverse("category-list")

    # ----------------------------------------------
    # LIST CATEGORIES
    # ----------------------------------------------

    def test_get_all_categories(self):
        """Test retrieving all categories."""

        Category.objects.create(**self.category_data)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(get_results(response)), 1)

    def test_get_empty_category_list(self):
        """Test retrieving categories when none exist."""

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(get_results(response)), 0)

    def test_category_response_structure(self):
        """Test that category responses contain expected fields."""

        Category.objects.create(**self.category_data)

        response = self.client.get(self.list_url)

        category = get_results(response)[0]

        expected_fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "updated_at"
        ]

        for field in expected_fields:
            self.assertIn(field, category)

    # ----------------------------------------------
    # CREATE CATEGORY
    # ----------------------------------------------

    def test_create_category(self):
        """Test creating a category with valid data."""

        response = self.client.post(
            self.list_url,
            self.category_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Category.objects.count(), 1)

    def test_create_category_with_invalid_data(self):
        """Test that invalid category data is rejected."""

        response = self.client.post(
            self.list_url,
            {"description": "Electronic products"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Category.objects.count(), 0)

    def test_create_category_with_duplicate_name(self):
        """Test that duplicate category names are rejected."""

        Category.objects.create(**self.category_data)

        data = self.category_data.copy()
        data["slug"] = "another-slug"

        response = self.client.post(
            self.list_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_category_with_duplicate_slug(self):
        """Test that duplicate category slugs are rejected."""

        Category.objects.create(**self.category_data)

        data = self.category_data.copy()
        data["name"] = "Computers"

        response = self.client.post(
            self.list_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ----------------------------------------------
    # RETRIEVE CATEGORY
    # ----------------------------------------------

    def test_get_single_category(self):
        """Test retrieving an existing category."""

        category = Category.objects.create(**self.category_data)

        detail_url = reverse(
            "category-detail",
            kwargs={"pk": category.pk}
        )

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["name"], "Electronics")

    def test_get_nonexistent_category(self):
        """Test retrieving a category that does not exist."""

        detail_url = reverse(
            "category-detail",
            kwargs={"pk": 999999}
        )

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------
    # UPDATE CATEGORY
    # ----------------------------------------------

    def test_update_category(self):
        """Test completely updating a category using PUT."""

        category = Category.objects.create(**self.category_data)

        updated_data = {
            "name": "Computers",
            "slug": "computers",
            "description": "Computer products",
            "is_active": True
        }

        detail_url = reverse(
            "category-detail",
            kwargs={"pk": category.pk}
        )

        response = self.client.put(
            detail_url,
            updated_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        category.refresh_from_db()

        self.assertEqual(category.name, "Computers")

    def test_partial_update_category(self):
        """Test partially updating a category using PATCH."""

        category = Category.objects.create(**self.category_data)

        detail_url = reverse(
            "category-detail",
            kwargs={"pk": category.pk}
        )

        response = self.client.patch(
            detail_url,
            {"description": "Updated description"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        category.refresh_from_db()

        self.assertEqual(
            category.description,
            "Updated description"
        )

        self.assertEqual(category.name, "Electronics")

    def test_update_category_with_invalid_data(self):
        """Test that invalid category updates are rejected."""

        category = Category.objects.create(**self.category_data)

        detail_url = reverse(
            "category-detail",
            kwargs={"pk": category.pk}
        )

        response = self.client.patch(
            detail_url,
            {"name": ""},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_nonexistent_category(self):
        """Test updating a category that does not exist."""

        detail_url = reverse(
            "category-detail",
            kwargs={"pk": 999999}
        )

        response = self.client.patch(
            detail_url,
            {"name": "Computers"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------
    # DELETE CATEGORY
    # ----------------------------------------------

    def test_delete_category(self):
        """Test deleting an existing category without products."""

        category = Category.objects.create(**self.category_data)

        detail_url = reverse(
            "category-detail",
            kwargs={"pk": category.pk}
        )

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(
            Category.objects.filter(pk=category.pk).exists()
        )

    def test_delete_nonexistent_category(self):
        """Test deleting a category that does not exist."""

        detail_url = reverse(
            "category-detail",
            kwargs={"pk": 999999}
        )

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)