# Shopper Backend

Python-based REST API for the Shopper application, built with FastAPI.

## Features

- **User Authentication**: JWT-based authentication with secure password hashing
- **Product Management**: CRUD operations for products with search functionality
- **Price Tracking**: Store and compare prices across multiple retailers
- **Wishlist**: Users can save products and set target prices for alerts

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get access token

### Users
- `GET /api/v1/users/me` - Get current user info
- `PUT /api/v1/users/me` - Update current user

### Products
- `GET /api/v1/products` - List products (with search)
- `GET /api/v1/products/{id}` - Get product details
- `POST /api/v1/products` - Create a product
- `PUT /api/v1/products/{id}` - Update a product
- `DELETE /api/v1/products/{id}` - Delete a product
- `POST /api/v1/products/{id}/prices` - Add price for a product
- `GET /api/v1/products/{id}/prices` - Get prices for a product

### Wishlist
- `GET /api/v1/wishlist` - Get user's wishlist
- `POST /api/v1/wishlist` - Add product to wishlist
- `PUT /api/v1/wishlist/{id}` - Update wishlist item
- `DELETE /api/v1/wishlist/{id}` - Remove from wishlist

## Testing

```bash
pytest tests/ -v
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py          # API dependencies
│   │   └── routes/          # API route handlers
│   ├── core/
│   │   ├── config.py        # Application settings
│   │   └── security.py      # Authentication utilities
│   ├── db/
│   │   └── database.py      # Database configuration
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── main.py              # FastAPI application
├── tests/                   # Test files
└── requirements.txt         # Python dependencies
```
