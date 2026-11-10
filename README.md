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
- Order management
- Payment integration using Stripe
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
├── payments/       # Payment processing
│
├── config/         # Project configuration
├── manage.py
└── README.md
```

## Development Status

The initial project setup and configuration are complete.

| Application | Status |
|---|---|
| Project Setup | Completed |
| Accounts | Completed |
| Products | Completed |
| Carts | In Progress |
| Orders | Planned |
| Payments | Planned |
| Final Integration | Planned |
| Deployment | Planned |

### Completed Work

**Accounts**
- Custom user model
- User registration
- JWT authentication
- Authentication and permission testing

**Products**
- Product and category models
- Serializers and validation
- CRUD API endpoints
- Staff-based permissions
- Filtering, searching, and ordering
- Pagination
- Automated tests
- Swagger API documentation

## API Documentation

Interactive API documentation is provided using:

- Swagger UI
- ReDoc

Documentation will be expanded as additional applications are developed.

## Development

This project is currently under active development. New features, automated tests, and documentation are being added incrementally.

## Version Control

Git and GitHub are used for version control and feature-based development.