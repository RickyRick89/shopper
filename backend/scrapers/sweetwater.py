"""Sweetwater web scraper for musical instruments."""

from typing import Any, Optional

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, ScrapedProduct


class SweetwaterScraper(BaseScraper):
    """Scraper for Sweetwater.com musical instrument retailer."""

    RETAILER_NAME = "Sweetwater"
    BASE_URL = "https://www.sweetwater.com"

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        max_results: int = 20,
        **kwargs: Any,
    ) -> list[ScrapedProduct]:
        """Search for products on Sweetwater.

        Args:
            query: Search query string
            category: Optional category filter
            max_results: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of scraped products
        """
        search_url = f"{self.BASE_URL}/store/search?s={query}"

        soup = self._get_soup(search_url)
        if soup is None:
            return []

        return self._parse_search_results(soup, max_results)

    def _parse_search_results(
        self,
        soup: BeautifulSoup,
        max_results: int,
    ) -> list[ScrapedProduct]:
        """Parse search results page.

        Args:
            soup: BeautifulSoup parsed page
            max_results: Maximum results to return

        Returns:
            List of scraped products
        """
        products: list[ScrapedProduct] = []

        # Find product cards in search results
        product_cards = soup.find_all("article", class_="product-card")

        for card in product_cards[:max_results]:
            product = self._parse_product_card(card)
            if product:
                products.append(product)

        return products

    def _parse_product_card(
        self,
        card: BeautifulSoup,
    ) -> Optional[ScrapedProduct]:
        """Parse a single product card from search results.

        Args:
            card: BeautifulSoup element for the product card

        Returns:
            ScrapedProduct or None if parsing failed
        """
        try:
            # Extract product name
            name_elem = card.find("h2", class_="product-card__name")
            if not name_elem:
                name_elem = card.find("a", class_="product-card__title")
            name = name_elem.get_text(strip=True) if name_elem else None

            if not name:
                return None

            # Extract price
            price_elem = card.find("span", class_="product-card__price")
            if not price_elem:
                price_elem = card.find("div", class_="price")
            price_str = price_elem.get_text(strip=True) if price_elem else ""
            price = self._normalize_price(price_str)

            if price is None:
                return None

            # Extract URL
            link_elem = card.find("a", href=True)
            url = self._normalize_url(link_elem["href"]) if link_elem else ""

            # Extract image
            img_elem = card.find("img")
            image_url = None
            if img_elem:
                image_url = img_elem.get("src") or img_elem.get("data-src")
                if image_url:
                    image_url = self._normalize_url(image_url)

            # Extract brand
            brand = self._extract_brand_from_name(name)

            # Determine category
            category = self._categorize_product(name)

            # Check stock status
            out_of_stock_elem = card.find(
                "span",
                string=lambda s: s and "out of stock" in s.lower() if s else False,
            )
            in_stock = out_of_stock_elem is None

            return ScrapedProduct(
                name=name,
                price=price,
                url=url,
                brand=brand,
                category=category,
                image_url=image_url,
                in_stock=in_stock,
                retailer=self.RETAILER_NAME,
                location=self._extract_location(
                    city="Fort Wayne",
                    state="IN",
                    zip_code="46818",
                    country="US",
                ),
            )

        except (AttributeError, TypeError, KeyError):
            return None

    def get_product(self, url: str) -> Optional[ScrapedProduct]:
        """Get detailed product information from a product page.

        Args:
            url: Product page URL

        Returns:
            ScrapedProduct or None if not found
        """
        soup = self._get_soup(url)
        if soup is None:
            return None

        return self._parse_product_page(soup, url)

    def _parse_product_page(
        self,
        soup: BeautifulSoup,
        url: str,
    ) -> Optional[ScrapedProduct]:
        """Parse a product detail page.

        Args:
            soup: BeautifulSoup parsed page
            url: Product URL

        Returns:
            ScrapedProduct or None if parsing failed
        """
        try:
            # Extract product name
            name_elem = soup.find("h1", class_="product__name")
            if not name_elem:
                name_elem = soup.find("h1", itemprop="name")
            name = name_elem.get_text(strip=True) if name_elem else None

            if not name:
                return None

            # Extract price
            price_elem = soup.find("meta", itemprop="price")
            if price_elem:
                price_str = price_elem.get("content", "")
            else:
                price_elem = soup.find("span", class_="product__price")
                price_str = price_elem.get_text(strip=True) if price_elem else ""

            price = self._normalize_price(price_str)
            if price is None:
                return None

            # Extract description
            desc_elem = soup.find("div", class_="product__description")
            if not desc_elem:
                desc_elem = soup.find("div", itemprop="description")
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # Extract image
            img_elem = soup.find("img", class_="product__image")
            if not img_elem:
                img_elem = soup.find("meta", itemprop="image")
            image_url = None
            if img_elem:
                image_url = img_elem.get("src") or img_elem.get("content")
                if image_url:
                    image_url = self._normalize_url(image_url)

            # Extract SKU
            sku_elem = soup.find("meta", itemprop="sku")
            sku = sku_elem.get("content") if sku_elem else None

            # Extract brand
            brand_elem = soup.find("meta", itemprop="brand")
            brand = brand_elem.get("content") if brand_elem else None
            if not brand:
                brand = self._extract_brand_from_name(name)

            # Determine category
            category = self._categorize_product(name, description or "")

            # Check stock status
            stock_elem = soup.find("meta", itemprop="availability")
            in_stock = True
            if stock_elem:
                availability = stock_elem.get("content", "")
                in_stock = "InStock" in availability

            return ScrapedProduct(
                name=name,
                price=price,
                url=url,
                brand=brand,
                category=category,
                description=description,
                image_url=image_url,
                in_stock=in_stock,
                retailer=self.RETAILER_NAME,
                sku=sku,
                location=self._extract_location(
                    city="Fort Wayne",
                    state="IN",
                    zip_code="46818",
                    country="US",
                ),
            )

        except (AttributeError, TypeError, KeyError):
            return None
