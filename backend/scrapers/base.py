"""Base scraper class with common functionality for web scraping."""

import time
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class ScraperConfig:
    """Configuration for scraper behavior."""

    # Rate limiting
    requests_per_minute: int = 10
    request_timeout: int = 30

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0

    # User agent for requests
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


@dataclass
class ScrapedProduct:
    """Normalized product data from scraped sources."""

    # Core product info
    name: str
    price: float
    currency: str = "USD"
    url: str = ""

    # Product details
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

    # Availability
    in_stock: bool = True
    condition: str = "new"

    # Retailer info
    retailer: str = ""
    sku: Optional[str] = None

    # Location info for geolocation
    location: Optional[dict[str, Any]] = None

    # Metadata
    scraped_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "price": self.price,
            "currency": self.currency,
            "url": self.url,
            "brand": self.brand,
            "model": self.model,
            "category": self.category,
            "description": self.description,
            "image_url": self.image_url,
            "in_stock": self.in_stock,
            "condition": self.condition,
            "retailer": self.retailer,
            "sku": self.sku,
            "location": self.location,
            "scraped_at": self.scraped_at.isoformat(),
        }


class BaseScraper(ABC):
    """Base class for all web scrapers."""

    # Retailer name - must be set by subclasses
    RETAILER_NAME: str = ""

    # Base URL for the retailer
    BASE_URL: str = ""

    def __init__(self, config: Optional[ScraperConfig] = None):
        """Initialize the scraper with configuration.

        Args:
            config: Scraper configuration. Uses defaults if not provided.
        """
        self.config = config or ScraperConfig()
        self._last_request_time: float = 0.0
        self._session: Optional[requests.Session] = None

    @property
    def session(self) -> requests.Session:
        """Get or create a requests session."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": self.config.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            })
        return self._session

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if self.config.requests_per_minute <= 0:
            return

        min_interval = 60.0 / self.config.requests_per_minute
        elapsed = time.monotonic() - self._last_request_time

        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

        self._last_request_time = time.monotonic()

    def _make_request(
        self,
        url: str,
        method: str = "GET",
        **kwargs: Any,
    ) -> Optional[requests.Response]:
        """Make an HTTP request with rate limiting and retries.

        Args:
            url: URL to request
            method: HTTP method
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object or None if all retries failed
        """
        self._rate_limit()

        kwargs.setdefault("timeout", self.config.request_timeout)

        for attempt in range(self.config.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException:
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                continue

        return None

    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL and parse it with BeautifulSoup.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if request failed
        """
        response = self._make_request(url)
        if response is None:
            return None

        return BeautifulSoup(response.text, "html.parser")

    def _normalize_price(self, price_str: str) -> Optional[float]:
        """Parse a price string into a float.

        Args:
            price_str: Price string like "$1,234.56" or "1234.56 USD"

        Returns:
            Float price value or None if parsing failed
        """
        if not price_str:
            return None

        # Remove currency symbols and whitespace
        cleaned = re.sub(r"[^\d.,]", "", price_str)

        # Handle European format (1.234,56) vs US format (1,234.56)
        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                # European format
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                # US format
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            # Could be European decimal or US thousands separator
            parts = cleaned.split(",")
            if len(parts) == 2 and len(parts[1]) == 2:
                # European decimal
                cleaned = cleaned.replace(",", ".")
            else:
                # US thousands
                cleaned = cleaned.replace(",", "")

        try:
            return float(cleaned)
        except ValueError:
            return None

    def _normalize_url(self, url: str, base_url: Optional[str] = None) -> str:
        """Normalize a URL to be absolute.

        Args:
            url: URL to normalize (can be relative or absolute)
            base_url: Base URL for relative URLs

        Returns:
            Absolute URL string
        """
        if not url:
            return ""

        # Already absolute
        if urlparse(url).scheme:
            return url

        # Use provided base or class default
        base = base_url or self.BASE_URL
        return urljoin(base, url)

    def _extract_location(
        self,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        country: str = "US",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Optional[dict[str, Any]]:
        """Extract and normalize location data.

        Args:
            address: Street address
            city: City name
            state: State/province code
            zip_code: ZIP/postal code
            country: Country code (default US)
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            Location dictionary or None if no location data
        """
        # Check if we have any location data
        has_address = any([address, city, state, zip_code])
        has_coords = latitude is not None and longitude is not None

        if not has_address and not has_coords:
            return None

        location: dict[str, Any] = {"country": country}

        if address:
            location["address"] = address.strip()
        if city:
            location["city"] = city.strip()
        if state:
            # Truncate to 2 chars for US state codes; international codes preserved as-is
            state_clean = state.strip().upper()
            location["state"] = state_clean[:2] if len(state_clean) > 2 else state_clean
        if zip_code:
            # Normalize US zip codes
            zip_clean = re.sub(r"[^\d-]", "", zip_code)
            location["zip_code"] = zip_clean[:10]
        if latitude is not None:
            location["latitude"] = latitude
        if longitude is not None:
            location["longitude"] = longitude

        return location

    def _extract_brand_from_name(self, name: str) -> Optional[str]:
        """Try to extract brand from product name.

        Common musical instrument brands are checked first word or common patterns.

        Args:
            name: Product name

        Returns:
            Brand name if found, None otherwise
        """
        if not name:
            return None

        # Common musical instrument brands
        known_brands = [
            "Fender", "Gibson", "Taylor", "Martin", "Yamaha", "Roland",
            "Ibanez", "PRS", "Epiphone", "Squier", "Gretsch", "Jackson",
            "ESP", "Schecter", "Rickenbacker", "Guild", "Takamine",
            "Korg", "Boss", "Marshall", "Vox", "Mesa Boogie",
            "Orange", "Line 6", "Blackstar", "Moog", "Nord",
            "Pearl", "Zildjian", "DW", "Ludwig", "Tama", "Mapex",
            "Shure", "Sennheiser", "Audio-Technica", "AKG", "Neumann",
        ]

        name_lower = name.lower()

        for brand in known_brands:
            if name_lower.startswith(brand.lower()):
                return brand
            if f" {brand.lower()} " in f" {name_lower} ":
                return brand

        # Fall back to first word if it looks like a brand (capitalized)
        first_word = name.split()[0] if name.split() else None
        if first_word and first_word[0].isupper() and len(first_word) > 2:
            return first_word

        return None

    def _categorize_product(self, name: str, description: str = "") -> Optional[str]:
        """Categorize a musical instrument product.

        Args:
            name: Product name
            description: Product description

        Returns:
            Category string or None
        """
        text = f"{name} {description}".lower()

        categories = {
            "electric guitars": [
                "electric guitar", "strat", "stratocaster", "telecaster",
                "les paul", "sg ", "flying v", "explorer",
            ],
            "acoustic guitars": [
                "acoustic guitar", "dreadnought", "concert guitar",
                "parlor guitar", "classical guitar", "nylon string",
            ],
            "bass guitars": [
                "bass guitar", "electric bass", "precision bass",
                "jazz bass", "p-bass", "j-bass",
            ],
            "amplifiers": [
                "amplifier", "amp ", "combo amp", "head amp",
                "cabinet", "tube amp", "solid state",
            ],
            "effects pedals": [
                "pedal", "effect", "overdrive", "distortion",
                "reverb", "delay", "chorus", "phaser",
            ],
            "drums": [
                "drum", "snare", "kick", "hi-hat", "cymbal",
                "drum kit", "drum set", "percussion",
            ],
            "keyboards": [
                "keyboard", "piano", "synthesizer", "synth",
                "midi controller", "workstation",
            ],
            "microphones": [
                "microphone", "mic ", "condenser", "dynamic mic",
                "ribbon mic", "vocal mic",
            ],
            "accessories": [
                "string", "pick", "strap", "case", "stand",
                "tuner", "capo", "cable", "adapter",
            ],
        }

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category

        return None

    @abstractmethod
    def search(self, query: str, **kwargs: Any) -> list[ScrapedProduct]:
        """Search for products matching a query.

        Args:
            query: Search query string
            **kwargs: Additional search parameters

        Returns:
            List of scraped products
        """
        pass

    @abstractmethod
    def get_product(self, url: str) -> Optional[ScrapedProduct]:
        """Get detailed product information from a product URL.

        Args:
            url: Product page URL

        Returns:
            Scraped product or None if not found
        """
        pass

    def close(self) -> None:
        """Close the scraper session and clean up resources."""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self) -> "BaseScraper":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.close()
