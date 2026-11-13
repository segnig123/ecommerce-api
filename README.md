# E-commerce REST API

A backend e-commerce application built with **Django REST Framework** and **PostgreSQL**. The project provides a RESTful API for managing users, products, shopping carts, orders, and payments.

## Technologies

- Python
- Django
- Django REST Framework
- PostgreSQL
- JWT Authentication
- Stripe API
- Git and GitHub

## Core Features

- User registration and authentication
- JWT-based authentication
- Custom user model
- Product and category management
- Shopping cart management
- Order creation and management
- Payment integration using Stripe Checkout
- Stripe webhook integration
- Product filtering, searching, and ordering
- API pagination
- Role-based permissions
- API documentation with Swagger and ReDoc
- Automated testing

## Project Structure

The application is organized into independent Django applications, each responsible for a specific part of the system.

```text
ecommerce_api/
│
├── accounts/       # User management and authentication
├── products/       # Products and categories
├── carts/          # Shopping cart functionality
├── orders/         # Order management
├── payments/       # Payment processing and Stripe integration
│
├── config/         # Project configuration
├── manage.py
└── README.md
```

## Development Status

The core backend applications and their integration are complete. The project has passed the full automated test suite.

| Application | Status |
|---|---|
| Project Setup | Completed |
| Accounts | Completed |
| Products | Completed |
| Carts | Completed |
| Orders | Completed |
| Payments | Completed |
| Final Integration | Completed |
| Deployment | Planned |

## Completed Work

### Accounts

- Custom user model
- User registration
- JWT authentication
- Login and token refresh
- Authentication and permission testing

### Products

- Product and category models
- Serializers and validation
- CRUD API endpoints
- Staff-based permissions
- Filtering, searching, and ordering
- Pagination
- Automated tests
- Swagger API documentation

### Carts

- Shopping cart and cart item models
- Add products to cart
- Retrieve cart details
- Update cart items
- Remove cart items
- Calculate item subtotals and cart totals
- Serializer validation
- Automated tests

### Orders

- Order and order item models
- Create orders from shopping carts
- Order item snapshots
- Order management endpoints
- Order status management
- Customer ownership permissions
- Order validation
- Automated tests

### Payments

- Payment model and payment status management
- Stripe Checkout integration
- Secure checkout session creation
- Stripe webhook signature verification
- Successful payment processing
- Failed and expired payment handling
- Automatic order confirmation after successful payment
- Webhook event idempotency using Stripe event IDs
- Automated payment and webhook tests

## API Documentation

Interactive API documentation is provided using **drf-spectacular**:

- Swagger UI
- ReDoc
- OpenAPI schema

The documentation describes available API endpoints, request formats, responses, and authentication requirements.

## Payment Integration

The project uses Stripe Checkout for payment processing.

### Payment Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/payments/` | Create a payment and Stripe Checkout session |
| POST | `/api/payments/webhook/` | Receive Stripe webhook events |

Customers create payments for their orders and are redirected to Stripe Checkout to complete payment.

The webhook endpoint handles:

- `checkout.session.completed`
- `checkout.session.expired`
- `payment_intent.payment_failed`

Webhook signatures are verified, and processed event IDs are stored to prevent duplicate processing.

### Environment Configuration

The following environment variables are required:

```env
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
STRIPE_SUCCESS_URL=http://localhost:8000/payment/success/
STRIPE_CANCEL_URL=http://localhost:8000/payment/cancel/
```

Never commit secret keys or your `.env` file to GitHub.

## Automated Testing

Automated tests are implemented across the applications to verify:

- Model behavior and database constraints
- Serializer validation
- API endpoints and responses
- Authentication and permissions
- Object ownership
- Payment processing
- Stripe webhook handling

Run all project tests using:

```bash
python manage.py test
```

## Development

The core backend development is complete. The next stages include final project improvements, deployment preparation, and production deployment.

## Version Control

Git and GitHub are used for version control and feature-based development.

Each major application is developed in its own feature branch, tested, and merged into the main branch after completion.