"""Web scrapers for musical instrument retailers."""

from scrapers.base import BaseScraper, ScrapedProduct, ScraperConfig
from scrapers.sweetwater import SweetwaterScraper
from scrapers.reverb import ReverbScraper
from scrapers.guitar_center import GuitarCenterScraper

__all__ = [
    "BaseScraper",
    "ScrapedProduct",
    "ScraperConfig",
    "SweetwaterScraper",
    "ReverbScraper",
    "GuitarCenterScraper",
]
