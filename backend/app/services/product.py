"""Product service for product queries and management."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.product import Price, Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_product(db: Session, product_id: int) -> Optional[Product]:
    """
    Get a product by ID.

    Args:
        db: Database session
        product_id: Product ID

    Returns:
        Product if found, None otherwise
    """
    return db.query(Product).filter(Product.id == product_id).first()


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    query: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
) -> List[Product]:
    """
    Get a list of products with optional filtering.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        query: Text search query for name/description
        category: Filter by category
        brand: Filter by brand

    Returns:
        List of products
    """
    from sqlalchemy import or_

    products_query = db.query(Product)

    if query:
        search_pattern = f"%{query}%"
        products_query = products_query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern),
            )
        )

    if category:
        products_query = products_query.filter(Product.category == category)

    if brand:
        products_query = products_query.filter(Product.brand == brand)

    return products_query.offset(skip).limit(limit).all()


def create_product(db: Session, product_data: ProductCreate) -> Product:
    """
    Create a new product.

    Args:
        db: Database session
        product_data: Product creation data

    Returns:
        Created product
    """
    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session, product_id: int, product_update: ProductUpdate
) -> Optional[Product]:
    """
    Update an existing product.

    Args:
        db: Database session
        product_id: Product ID
        product_update: Product update data

    Returns:
        Updated product if found, None otherwise
    """
    product = get_product(db, product_id)
    if not product:
        return None

    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    """
    Delete a product.

    Args:
        db: Database session
        product_id: Product ID

    Returns:
        True if deleted, False if not found
    """
    product = get_product(db, product_id)
    if not product:
        return False

    db.delete(product)
    db.commit()
    return True


def get_product_prices(db: Session, product_id: int) -> List[Price]:
    """
    Get all prices for a product.

    Args:
        db: Database session
        product_id: Product ID

    Returns:
        List of prices for the product
    """
    product = get_product(db, product_id)
    if not product:
        return []
    return product.prices


def add_product_price(
    db: Session,
    product_id: int,
    retailer: str,
    price: float,
    currency: str = "USD",
    url: Optional[str] = None,
    in_stock: bool = True,
) -> Optional[Price]:
    """
    Add a price entry for a product.

    Args:
        db: Database session
        product_id: Product ID
        retailer: Retailer name
        price: Price value
        currency: Currency code
        url: Product URL at retailer
        in_stock: Stock availability

    Returns:
        Created price if product found, None otherwise
    """
    product = get_product(db, product_id)
    if not product:
        return None

    price_entry = Price(
        product_id=product_id,
        retailer=retailer,
        price=price,
        currency=currency,
        url=url,
        in_stock=in_stock,
    )
    db.add(price_entry)
    db.commit()
    db.refresh(price_entry)
    return price_entry


def get_lowest_price(db: Session, product_id: int) -> Optional[Price]:
    """
    Get the lowest current price for a product.

    Args:
        db: Database session
        product_id: Product ID

    Returns:
        Lowest price entry if available, None otherwise
    """
    return (
        db.query(Price)
        .filter(Price.product_id == product_id, Price.in_stock.is_(True))
        .order_by(Price.price.asc())
        .first()
    )


def get_products_by_category(
    db: Session, category: str, skip: int = 0, limit: int = 20
) -> List[Product]:
    """
    Get products by category.

    Args:
        db: Database session
        category: Category name
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of products in the category
    """
    return (
        db.query(Product)
        .filter(Product.category.ilike(f"%{category}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_products_by_brand(
    db: Session, brand: str, skip: int = 0, limit: int = 20
) -> List[Product]:
    """
    Get products by brand.

    Args:
        db: Database session
        brand: Brand name
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of products from the brand
    """
    return (
        db.query(Product)
        .filter(Product.brand.ilike(f"%{brand}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_in_stock_products(
    db: Session, skip: int = 0, limit: int = 20
) -> List[Product]:
    """
    Get products that are currently in stock at any retailer.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of in-stock products
    """
    return (
        db.query(Product)
        .join(Price)
        .filter(Price.in_stock.is_(True))
        .distinct()
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_products(
    db: Session,
    query: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
) -> int:
    """
    Count products with optional filtering.

    Args:
        db: Database session
        query: Text search query
        category: Filter by category
        brand: Filter by brand

    Returns:
        Number of matching products
    """
    from sqlalchemy import func, or_

    products_query = db.query(func.count(Product.id))

    if query:
        search_pattern = f"%{query}%"
        products_query = products_query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern),
            )
        )

    if category:
        products_query = products_query.filter(Product.category == category)

    if brand:
        products_query = products_query.filter(Product.brand == brand)

    return products_query.scalar()
