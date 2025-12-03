"""Tests for the web scraping module."""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from scrapers.base import BaseScraper, ScrapedProduct, ScraperConfig


class TestScraperConfig:
    """Tests for ScraperConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ScraperConfig()
        assert config.requests_per_minute == 10
        assert config.request_timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert "Mozilla" in config.user_agent

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ScraperConfig(
            requests_per_minute=5,
            request_timeout=60,
            max_retries=5,
        )
        assert config.requests_per_minute == 5
        assert config.request_timeout == 60
        assert config.max_retries == 5


class TestScrapedProduct:
    """Tests for ScrapedProduct dataclass."""

    def test_minimal_product(self):
        """Test creating a product with minimal data."""
        product = ScrapedProduct(
            name="Test Guitar",
            price=999.99,
        )
        assert product.name == "Test Guitar"
        assert product.price == 999.99
        assert product.currency == "USD"
        assert product.in_stock is True
        assert product.condition == "new"

    def test_full_product(self):
        """Test creating a product with all fields."""
        product = ScrapedProduct(
            name="Fender Stratocaster",
            price=1499.99,
            currency="USD",
            url="https://example.com/product",
            brand="Fender",
            model="Stratocaster",
            category="electric guitars",
            description="Classic electric guitar",
            image_url="https://example.com/image.jpg",
            in_stock=True,
            condition="new",
            retailer="Test Store",
            sku="FEN-STRAT-001",
            location={"city": "Nashville", "state": "TN"},
        )
        assert product.brand == "Fender"
        assert product.category == "electric guitars"
        assert product.location["city"] == "Nashville"

    def test_to_dict(self):
        """Test converting product to dictionary."""
        product = ScrapedProduct(
            name="Test Product",
            price=100.00,
            retailer="Test",
        )
        data = product.to_dict()
        assert data["name"] == "Test Product"
        assert data["price"] == 100.00
        assert data["retailer"] == "Test"
        assert "scraped_at" in data


class ConcreteScraper(BaseScraper):
    """Concrete implementation for testing BaseScraper."""

    RETAILER_NAME = "Test Retailer"
    BASE_URL = "https://test.example.com"

    def search(self, query, **kwargs):
        return []

    def get_product(self, url):
        return None


class TestBaseScraper:
    """Tests for BaseScraper base class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        scraper = ConcreteScraper()
        assert scraper.config.requests_per_minute == 10
        assert scraper.RETAILER_NAME == "Test Retailer"

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = ScraperConfig(requests_per_minute=5)
        scraper = ConcreteScraper(config=config)
        assert scraper.config.requests_per_minute == 5

    def test_session_creation(self):
        """Test that session is created on first access."""
        scraper = ConcreteScraper()
        assert scraper._session is None
        session = scraper.session
        assert session is not None
        assert scraper._session is session

    def test_context_manager(self):
        """Test context manager behavior."""
        with ConcreteScraper() as scraper:
            _ = scraper.session
            assert scraper._session is not None
        assert scraper._session is None

    def test_normalize_price_usd(self):
        """Test normalizing USD price strings."""
        scraper = ConcreteScraper()
        assert scraper._normalize_price("$1,234.56") == 1234.56
        assert scraper._normalize_price("$99.99") == 99.99
        assert scraper._normalize_price("1234.56 USD") == 1234.56
        assert scraper._normalize_price("$1,000") == 1000.0

    def test_normalize_price_european(self):
        """Test normalizing European price strings."""
        scraper = ConcreteScraper()
        assert scraper._normalize_price("1.234,56€") == 1234.56
        assert scraper._normalize_price("99,99 EUR") == 99.99

    def test_normalize_price_invalid(self):
        """Test normalizing invalid price strings."""
        scraper = ConcreteScraper()
        assert scraper._normalize_price("") is None
        assert scraper._normalize_price("Free") is None
        assert scraper._normalize_price("Call for price") is None

    def test_normalize_url_absolute(self):
        """Test normalizing absolute URLs."""
        scraper = ConcreteScraper()
        url = "https://other.com/product"
        assert scraper._normalize_url(url) == url

    def test_normalize_url_relative(self):
        """Test normalizing relative URLs."""
        scraper = ConcreteScraper()
        assert scraper._normalize_url("/product/123") == "https://test.example.com/product/123"
        assert scraper._normalize_url("product/123") == "https://test.example.com/product/123"

    def test_normalize_url_empty(self):
        """Test normalizing empty URL."""
        scraper = ConcreteScraper()
        assert scraper._normalize_url("") == ""

    def test_extract_location_full(self):
        """Test extracting location with all fields."""
        scraper = ConcreteScraper()
        location = scraper._extract_location(
            address="123 Main St",
            city="Nashville",
            state="TN",
            zip_code="37203",
            country="US",
            latitude=36.1627,
            longitude=-86.7816,
        )
        assert location["address"] == "123 Main St"
        assert location["city"] == "Nashville"
        assert location["state"] == "TN"
        assert location["zip_code"] == "37203"
        assert location["latitude"] == 36.1627
        assert location["longitude"] == -86.7816

    def test_extract_location_partial(self):
        """Test extracting location with partial data."""
        scraper = ConcreteScraper()
        location = scraper._extract_location(city="Nashville", state="TN")
        assert location["city"] == "Nashville"
        assert location["state"] == "TN"
        assert "address" not in location

    def test_extract_location_none(self):
        """Test extracting location with no data."""
        scraper = ConcreteScraper()
        assert scraper._extract_location() is None

    def test_extract_brand_from_name(self):
        """Test extracting brand from product name."""
        scraper = ConcreteScraper()
        assert scraper._extract_brand_from_name("Fender Stratocaster") == "Fender"
        assert scraper._extract_brand_from_name("Gibson Les Paul Standard") == "Gibson"
        assert scraper._extract_brand_from_name("Taylor 214ce") == "Taylor"

    def test_extract_brand_from_name_unknown(self):
        """Test extracting brand from name with unknown brand."""
        scraper = ConcreteScraper()
        # Falls back to first word if capitalized
        assert scraper._extract_brand_from_name("CustomBrand Guitar") == "CustomBrand"

    def test_categorize_product_guitar(self):
        """Test categorizing guitar products."""
        scraper = ConcreteScraper()
        assert scraper._categorize_product("Fender Stratocaster Electric Guitar") == "electric guitars"
        assert scraper._categorize_product("Taylor 214ce Acoustic Guitar") == "acoustic guitars"
        assert scraper._categorize_product("Fender Jazz Bass") == "bass guitars"

    def test_categorize_product_other(self):
        """Test categorizing other instrument products."""
        scraper = ConcreteScraper()
        assert scraper._categorize_product("Marshall JCM800 Amplifier") == "amplifiers"
        assert scraper._categorize_product("Boss DS-1 Distortion Pedal") == "effects pedals"
        assert scraper._categorize_product("Pearl Export Drum Kit") == "drums"

    def test_categorize_product_unknown(self):
        """Test categorizing unknown products."""
        scraper = ConcreteScraper()
        assert scraper._categorize_product("Something Random") is None

    @patch("scrapers.base.time.sleep")
    def test_rate_limiting(self, mock_sleep):
        """Test that rate limiting is applied."""
        config = ScraperConfig(requests_per_minute=60)  # 1 per second
        scraper = ConcreteScraper(config=config)

        # First request, no sleep
        scraper._rate_limit()
        mock_sleep.assert_not_called()

        # Immediate second request should sleep
        scraper._rate_limit()
        mock_sleep.assert_called()

    @patch("scrapers.base.requests.Session")
    def test_make_request_success(self, mock_session_class):
        """Test successful HTTP request."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session

        scraper = ConcreteScraper()
        scraper._session = mock_session

        response = scraper._make_request("https://example.com")
        assert response == mock_response

    @patch("scrapers.base.requests.Session")
    @patch("scrapers.base.time.sleep")
    def test_make_request_retry(self, mock_sleep, mock_session_class):
        """Test HTTP request with retries."""
        import requests as req

        mock_session = MagicMock()
        mock_session.request.side_effect = [
            req.RequestException("Error"),
            req.RequestException("Error"),
            MagicMock(),  # Success on third try
        ]
        mock_session_class.return_value = mock_session

        scraper = ConcreteScraper()
        scraper._session = mock_session

        response = scraper._make_request("https://example.com")
        assert response is not None
        assert mock_session.request.call_count == 3


class TestSweetwaterScraper:
    """Tests for SweetwaterScraper."""

    def test_retailer_name(self):
        """Test retailer name is set correctly."""
        from scrapers.sweetwater import SweetwaterScraper

        scraper = SweetwaterScraper()
        assert scraper.RETAILER_NAME == "Sweetwater"
        assert "sweetwater.com" in scraper.BASE_URL

    @patch.object(BaseScraper, "_get_soup")
    def test_search_no_results(self, mock_get_soup):
        """Test search with no results."""
        from scrapers.sweetwater import SweetwaterScraper

        mock_get_soup.return_value = MagicMock(find_all=MagicMock(return_value=[]))

        scraper = SweetwaterScraper()
        results = scraper.search("nonexistent product")
        assert results == []

    @patch.object(BaseScraper, "_get_soup")
    def test_search_request_fails(self, mock_get_soup):
        """Test search when request fails."""
        from scrapers.sweetwater import SweetwaterScraper

        mock_get_soup.return_value = None

        scraper = SweetwaterScraper()
        results = scraper.search("guitar")
        assert results == []

    @patch.object(BaseScraper, "_get_soup")
    def test_get_product_not_found(self, mock_get_soup):
        """Test getting product that doesn't exist."""
        from scrapers.sweetwater import SweetwaterScraper

        mock_get_soup.return_value = None

        scraper = SweetwaterScraper()
        result = scraper.get_product("https://sweetwater.com/product/123")
        assert result is None


class TestReverbScraper:
    """Tests for ReverbScraper."""

    def test_retailer_name(self):
        """Test retailer name is set correctly."""
        from scrapers.reverb import ReverbScraper

        scraper = ReverbScraper()
        assert scraper.RETAILER_NAME == "Reverb"
        assert "reverb.com" in scraper.BASE_URL

    @patch.object(BaseScraper, "_get_soup")
    def test_search_no_results(self, mock_get_soup):
        """Test search with no results."""
        from scrapers.reverb import ReverbScraper

        mock_get_soup.return_value = MagicMock(find_all=MagicMock(return_value=[]))

        scraper = ReverbScraper()
        results = scraper.search("nonexistent product")
        assert results == []

    def test_parse_location_text(self):
        """Test parsing location text."""
        from scrapers.reverb import ReverbScraper

        scraper = ReverbScraper()
        location = scraper._parse_location_text("Nashville, TN, US")
        assert location["city"] == "Nashville"
        assert location["state"] == "TN"
        assert location["country"] == "US"

    def test_parse_location_text_partial(self):
        """Test parsing partial location text."""
        from scrapers.reverb import ReverbScraper

        scraper = ReverbScraper()
        location = scraper._parse_location_text("Los Angeles")
        assert location["city"] == "Los Angeles"

    def test_parse_location_text_empty(self):
        """Test parsing empty location text."""
        from scrapers.reverb import ReverbScraper

        scraper = ReverbScraper()
        assert scraper._parse_location_text("") is None


class TestGuitarCenterScraper:
    """Tests for GuitarCenterScraper."""

    def test_retailer_name(self):
        """Test retailer name is set correctly."""
        from scrapers.guitar_center import GuitarCenterScraper

        scraper = GuitarCenterScraper()
        assert scraper.RETAILER_NAME == "Guitar Center"
        assert "guitarcenter.com" in scraper.BASE_URL

    @patch.object(BaseScraper, "_get_soup")
    def test_search_no_results(self, mock_get_soup):
        """Test search with no results."""
        from scrapers.guitar_center import GuitarCenterScraper

        mock_get_soup.return_value = MagicMock(find_all=MagicMock(return_value=[]))

        scraper = GuitarCenterScraper()
        results = scraper.search("nonexistent product")
        assert results == []

    def test_get_store_inventory_empty(self):
        """Test getting store inventory returns empty list."""
        from scrapers.guitar_center import GuitarCenterScraper

        scraper = GuitarCenterScraper()
        inventory = scraper.get_store_inventory(
            "https://guitarcenter.com/product/123",
            "37203"
        )
        assert inventory == []
