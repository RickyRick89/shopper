"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from app.api.routes import auth, products, search, users, wishlist, alerts, price_history
from app.core.config import get_settings
from app.db.database import Base, SessionLocal, engine
from app.models.product import Price, Product

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)


def seed_sample_data() -> None:
    """Insert a small set of demo products if the database is empty."""

    db: Session = SessionLocal()
    try:
        if db.query(Product).count() > 0:
            return

        sax1 = Product(
            name="Yamaha YAS-280 Alto Saxophone",
            brand="Yamaha",
            category="Instruments",
            description="Student alto sax with case and mouthpiece.",
            image_url="https://example.com/yamaha-yas-280.jpg",
        )
        sax2 = Product(
            name="Jean Paul USA TS-400 Tenor Saxophone",
            brand="Jean Paul",
            category="Instruments",
            description="Tenor saxophone with deluxe carrying case.",
            image_url="https://example.com/jean-paul-ts-400.jpg",
        )
        sax3 = Product(
            name="Selmer Prelude AS711 Alto Sax",
            brand="Selmer",
            category="Instruments",
            description="Entry-level alto sax, great for beginners.",
            image_url="https://example.com/selmer-prelude-as711.jpg",
        )

        db.add_all([sax1, sax2, sax3])
        db.flush()  # assign IDs for prices

        prices = [
            Price(product_id=sax1.id, retailer="Sweetwater", price=1299.99, url="https://example.com/yamaha-yas-280/sweetwater"),
            Price(product_id=sax1.id, retailer="Guitar Center", price=1199.99, url="https://example.com/yamaha-yas-280/gc"),
            Price(product_id=sax2.id, retailer="Amazon", price=899.00, url="https://example.com/ts-400/amazon"),
            Price(product_id=sax2.id, retailer="Reverb", price=859.50, url="https://example.com/ts-400/reverb"),
            Price(product_id=sax3.id, retailer="Sweetwater", price=699.99, url="https://example.com/as711/sweetwater"),
        ]

        db.add_all(prices)
        db.commit()
    finally:
        db.close()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A modern shopping application for finding deals and tracking prices.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(products.router, prefix=settings.api_v1_prefix)
app.include_router(search.router, prefix=settings.api_v1_prefix)
app.include_router(wishlist.router, prefix=settings.api_v1_prefix)
app.include_router(alerts.router, prefix=settings.api_v1_prefix)
app.include_router(price_history.router, prefix=settings.api_v1_prefix)


# Seed demo data at startup so product search returns results immediately
seed_sample_data()


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
