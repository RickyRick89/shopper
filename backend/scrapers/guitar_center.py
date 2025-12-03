"""Guitar Center web scraper for musical instruments."""

from typing import Any, Optional

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, ScrapedProduct


class GuitarCenterScraper(BaseScraper):
    """Scraper for GuitarCenter.com musical instrument retailer."""

    RETAILER_NAME = "Guitar Center"
    BASE_URL = "https://www.guitarcenter.com"

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        max_results: int = 20,
        **kwargs: Any,
    ) -> list[ScrapedProduct]:
        """Search for products on Guitar Center.

        Args:
            query: Search query string
            category: Optional category filter
            max_results: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of scraped products
        """
        search_url = f"{self.BASE_URL}/search?Ntt={query}"

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

        # Find product tiles in search results
        product_tiles = soup.find_all("div", class_="product-tile")
        if not product_tiles:
            product_tiles = soup.find_all("li", class_="product-item")

        for tile in product_tiles[:max_results]:
            product = self._parse_product_tile(tile)
            if product:
                products.append(product)

        return products

    def _parse_product_tile(
        self,
        tile: BeautifulSoup,
    ) -> Optional[ScrapedProduct]:
        """Parse a single product tile from search results.

        Args:
            tile: BeautifulSoup element for the product tile

        Returns:
            ScrapedProduct or None if parsing failed
        """
        try:
            # Extract product name
            name_elem = tile.find("a", class_="product-name")
            if not name_elem:
                name_elem = tile.find("h3")
            name = name_elem.get_text(strip=True) if name_elem else None

            if not name:
                return None

            # Extract price
            price_elem = tile.find("span", class_="sale-price")
            if not price_elem:
                price_elem = tile.find("span", class_="price")
            price_str = price_elem.get_text(strip=True) if price_elem else ""
            price = self._normalize_price(price_str)

            if price is None:
                return None

            # Extract URL
            link_elem = tile.find("a", href=True)
            url = self._normalize_url(link_elem["href"]) if link_elem else ""

            # Extract image
            img_elem = tile.find("img")
            image_url = None
            if img_elem:
                image_url = img_elem.get("src") or img_elem.get("data-src")
                if image_url:
                    image_url = self._normalize_url(image_url)

            # Extract brand
            brand_elem = tile.find("span", class_="brand-name")
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            if not brand:
                brand = self._extract_brand_from_name(name)

            # Determine category
            category = self._categorize_product(name)

            # Check stock status
            out_of_stock = tile.find("span", class_="out-of-stock")
            in_stock = out_of_stock is None

            return ScrapedProduct(
                name=name,
                price=price,
                url=url,
                brand=brand,
                category=category,
                image_url=image_url,
                in_stock=in_stock,
                retailer=self.RETAILER_NAME,
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
            name_elem = soup.find("h1", class_="product-name")
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
                price_elem = soup.find("span", class_="sale-price")
                if not price_elem:
                    price_elem = soup.find("span", class_="price")
                price_str = price_elem.get_text(strip=True) if price_elem else ""

            price = self._normalize_price(price_str)
            if price is None:
                return None

            # Extract description
            desc_elem = soup.find("div", class_="product-description")
            if not desc_elem:
                desc_elem = soup.find("div", itemprop="description")
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # Extract image
            img_elem = soup.find("img", class_="product-image")
            if not img_elem:
                img_elem = soup.find("meta", property="og:image")
            image_url = None
            if img_elem:
                image_url = img_elem.get("src") or img_elem.get("content")
                if image_url:
                    image_url = self._normalize_url(image_url)

            # Extract SKU
            sku_elem = soup.find("span", class_="product-sku")
            if not sku_elem:
                sku_elem = soup.find("meta", itemprop="sku")
            sku = None
            if sku_elem:
                sku = sku_elem.get("content") or sku_elem.get_text(strip=True)

            # Extract brand
            brand_elem = soup.find("meta", itemprop="brand")
            brand = brand_elem.get("content") if brand_elem else None
            if not brand:
                brand_elem = soup.find("a", class_="brand-link")
                brand = brand_elem.get_text(strip=True) if brand_elem else None
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

            # Extract store location if available
            location = self._extract_store_location(soup)

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
                location=location,
            )

        except (AttributeError, TypeError, KeyError):
            return None

    def _extract_store_location(
        self,
        soup: BeautifulSoup,
    ) -> Optional[dict[str, Any]]:
        """Extract store location from product page.

        Args:
            soup: BeautifulSoup parsed page

        Returns:
            Location dictionary or None
        """
        try:
            store_elem = soup.find("div", class_="store-info")
            if not store_elem:
                return None

            # Extract address components
            address_elem = store_elem.find("span", class_="address")
            city_elem = store_elem.find("span", class_="city")
            state_elem = store_elem.find("span", class_="state")
            zip_elem = store_elem.find("span", class_="zip")

            address = address_elem.get_text(strip=True) if address_elem else None
            city = city_elem.get_text(strip=True) if city_elem else None
            state = state_elem.get_text(strip=True) if state_elem else None
            zip_code = zip_elem.get_text(strip=True) if zip_elem else None

            return self._extract_location(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
            )

        except (AttributeError, TypeError):
            return None

    def get_store_inventory(
        self,
        product_url: str,
        zip_code: str,
    ) -> list[dict[str, Any]]:
        """Get store inventory for a product near a zip code.

        Args:
            product_url: Product page URL
            zip_code: ZIP code to search near

        Returns:
            List of store inventory dictionaries
        """
        # TODO: Implement store inventory lookup via AJAX API
        # This requires JavaScript execution or direct API calls
        # to Guitar Center's inventory service
        return []
