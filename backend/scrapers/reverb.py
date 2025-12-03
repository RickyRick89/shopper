"""Reverb web scraper for musical instruments marketplace."""

from typing import Any, Optional

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, ScrapedProduct


class ReverbScraper(BaseScraper):
    """Scraper for Reverb.com musical instrument marketplace."""

    RETAILER_NAME = "Reverb"
    BASE_URL = "https://reverb.com"

    def search(
        self,
        query: str,
        condition: Optional[str] = None,
        max_results: int = 20,
        **kwargs: Any,
    ) -> list[ScrapedProduct]:
        """Search for products on Reverb.

        Args:
            query: Search query string
            condition: Filter by condition (new, used, all)
            max_results: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of scraped products
        """
        search_url = f"{self.BASE_URL}/marketplace?query={query}"

        if condition and condition.lower() in ("new", "used"):
            search_url += f"&condition={condition.lower()}"

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

        # Find product listings
        listings = soup.find_all("li", class_="grid-card")
        if not listings:
            listings = soup.find_all("div", class_="listing-row")

        for listing in listings[:max_results]:
            product = self._parse_listing(listing)
            if product:
                products.append(product)

        return products

    def _parse_listing(
        self,
        listing: BeautifulSoup,
    ) -> Optional[ScrapedProduct]:
        """Parse a single product listing.

        Args:
            listing: BeautifulSoup element for the listing

        Returns:
            ScrapedProduct or None if parsing failed
        """
        try:
            # Extract product name
            name_elem = listing.find("a", class_="grid-card__title")
            if not name_elem:
                name_elem = listing.find("h4")
            name = name_elem.get_text(strip=True) if name_elem else None

            if not name:
                return None

            # Extract price
            price_elem = listing.find("span", class_="grid-card__price")
            if not price_elem:
                price_elem = listing.find("div", class_="price")
            price_str = price_elem.get_text(strip=True) if price_elem else ""
            price = self._normalize_price(price_str)

            if price is None:
                return None

            # Extract URL
            link_elem = listing.find("a", href=True)
            url = self._normalize_url(link_elem["href"]) if link_elem else ""

            # Extract image
            img_elem = listing.find("img")
            image_url = None
            if img_elem:
                image_url = img_elem.get("src") or img_elem.get("data-src")
                if image_url:
                    image_url = self._normalize_url(image_url)

            # Extract condition
            condition_elem = listing.find("span", class_="condition")
            condition = "used"  # Default for Reverb
            if condition_elem:
                condition_text = condition_elem.get_text(strip=True).lower()
                if "new" in condition_text:
                    condition = "new"

            # Extract seller location
            location_elem = listing.find("span", class_="seller-location")
            if not location_elem:
                location_elem = listing.find("div", class_="location")
            location = None
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                location = self._parse_location_text(location_text)

            # Extract brand
            brand = self._extract_brand_from_name(name)

            # Determine category
            category = self._categorize_product(name)

            return ScrapedProduct(
                name=name,
                price=price,
                url=url,
                brand=brand,
                category=category,
                image_url=image_url,
                in_stock=True,  # Listed items are available
                condition=condition,
                retailer=self.RETAILER_NAME,
                location=location,
            )

        except (AttributeError, TypeError, KeyError):
            return None

    def _parse_location_text(self, location_text: str) -> Optional[dict[str, Any]]:
        """Parse location text like 'Nashville, TN, US'.

        Args:
            location_text: Location string

        Returns:
            Location dictionary or None
        """
        if not location_text:
            return None

        parts = [p.strip() for p in location_text.split(",")]

        city = None
        state = None
        country = "US"

        if len(parts) >= 1:
            city = parts[0]
        if len(parts) >= 2:
            state = parts[1]
        if len(parts) >= 3:
            country = parts[2]

        return self._extract_location(
            city=city,
            state=state,
            country=country,
        )

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
            name_elem = soup.find("h1", class_="listing-title")
            if not name_elem:
                name_elem = soup.find("h1")
            name = name_elem.get_text(strip=True) if name_elem else None

            if not name:
                return None

            # Extract price
            price_elem = soup.find("span", class_="price")
            if not price_elem:
                price_elem = soup.find("meta", itemprop="price")
            price_str = ""
            if price_elem:
                price_str = (
                    price_elem.get("content") or
                    price_elem.get_text(strip=True)
                )
            price = self._normalize_price(price_str)
            if price is None:
                return None

            # Extract description
            desc_elem = soup.find("div", class_="listing-description")
            if not desc_elem:
                desc_elem = soup.find("div", itemprop="description")
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # Extract image
            img_elem = soup.find("img", class_="listing-image")
            if not img_elem:
                img_elem = soup.find("meta", property="og:image")
            image_url = None
            if img_elem:
                image_url = img_elem.get("src") or img_elem.get("content")
                if image_url:
                    image_url = self._normalize_url(image_url)

            # Extract condition
            condition_elem = soup.find("span", class_="condition")
            condition = "used"
            if condition_elem:
                condition_text = condition_elem.get_text(strip=True).lower()
                if "new" in condition_text:
                    condition = "new"

            # Extract seller location
            location_elem = soup.find("span", class_="seller-location")
            location = None
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                location = self._parse_location_text(location_text)

            # Extract brand
            brand_elem = soup.find("a", class_="brand")
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            if not brand:
                brand = self._extract_brand_from_name(name)

            # Determine category
            category = self._categorize_product(name, description or "")

            return ScrapedProduct(
                name=name,
                price=price,
                url=url,
                brand=brand,
                category=category,
                description=description,
                image_url=image_url,
                in_stock=True,
                condition=condition,
                retailer=self.RETAILER_NAME,
                location=location,
            )

        except (AttributeError, TypeError, KeyError):
            return None
