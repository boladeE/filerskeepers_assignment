"""Main web scraper using httpx and BeautifulSoup."""

import asyncio
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.crawler.models import Book
from app.crawler.storage import BookStorage
from app.utils.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("scraper")


class BookScraper:
    """Web scraper for books.toscrape.com."""

    def __init__(self):
        """Initialize scraper."""
        self.base_url = settings.base_url
        self.storage = BookStorage()
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        self.crawled_urls: set[str] = set()

    async def _fetch_page(
        self, url: str, retry_count: int = 0
    ) -> Optional[httpx.Response]:
        """Fetch a page with retry logic.

        Args:
            url: URL to fetch
            retry_count: Current retry attempt

        Returns:
            HTTP response or None
        """
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(
                    timeout=settings.request_timeout
                ) as client:
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()
                    return response
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error for {url}: {e.response.status_code}")
                if retry_count < settings.max_retries:
                    await asyncio.sleep(settings.retry_delay * (2**retry_count))
                    return await self._fetch_page(url, retry_count + 1)
                return None
            except httpx.RequestError as e:
                logger.warning(f"Request error for {url}: {e}")
                if retry_count < settings.max_retries:
                    await asyncio.sleep(settings.retry_delay * (2**retry_count))
                    return await self._fetch_page(url, retry_count + 1)
                return None
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None

    def _parse_book_page(self, html: str, url: str) -> Optional[Book]:
        """Parse book details from HTML.

        Args:
            html: HTML content
            url: Source URL

        Returns:
            Book instance or None
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Extract book name
            name_elem = soup.select_one("h1")
            name = name_elem.get_text(strip=True) if name_elem else ""

            # Extract description
            desc_elem = soup.select_one("#product_description + p")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # Extract category
            category_elem = soup.select("ul.breadcrumb a")[-1]
            category = category_elem.get_text(strip=True) if category_elem else ""

            # Extract prices (excluding tax)
            price_excluding_tax_elem = soup.find("th", string="Price (excl. tax)")
            price_excluding_tax = 0.0
            if price_excluding_tax_elem:
                price_elem = price_excluding_tax_elem.find_next_sibling("td")
                if price_elem:
                    price_text = (
                        price_elem.get_text(strip=True)
                        .replace("£", "")
                        .replace("€", "")
                        .replace("$", "")
                    )
                    try:
                        price_excluding_tax = float(price_text)
                    except ValueError:
                        logger.warning(
                            f"Could not parse price excluding tax: {price_text}"
                        )

            # Extract prices (including tax)
            price_including_tax_elem = soup.find("th", string="Price (incl. tax)")
            price_including_tax = price_excluding_tax
            if price_including_tax_elem:
                price_elem = price_including_tax_elem.find_next_sibling("td")
                if price_elem:
                    price_text = (
                        price_elem.get_text(strip=True)
                        .replace("£", "")
                        .replace("€", "")
                        .replace("$", "")
                    )
                    try:
                        price_including_tax = float(price_text)
                    except ValueError:
                        logger.warning(
                            f"Could not parse price including tax: {price_text}"
                        )

            # Extract availability
            availability_elem = soup.find("th", string="Availability")
            availability = "Unknown"
            if availability_elem:
                availability_text = availability_elem.find_next_sibling("td")
                if availability_text:
                    availability = availability_text.get_text(strip=True)

            # Extract number of reviews
            reviews_elem = soup.find("th", string="Number of reviews")
            number_of_reviews = 0
            if reviews_elem:
                reviews_text = reviews_elem.find_next_sibling("td")
                if reviews_text:
                    try:
                        number_of_reviews = int(reviews_text.get_text(strip=True))
                    except ValueError:
                        pass

            # Extract image URL
            image_elem = soup.select_one("#product_gallery img")
            image_url = ""
            if image_elem:
                image_src = image_elem.get("src", "")
                # Convert relative URL to absolute
                image_url = urljoin(url, image_src.replace("../..", ""))

            # Extract rating
            rating_elem = soup.select_one("p.star-rating")
            rating = None
            if rating_elem:
                rating_classes = rating_elem.get("class", [])
                for cls in rating_classes:
                    if cls.startswith("One"):
                        rating = "One"
                        break
                    elif cls.startswith("Two"):
                        rating = "Two"
                        break
                    elif cls.startswith("Three"):
                        rating = "Three"
                        break
                    elif cls.startswith("Four"):
                        rating = "Four"
                        break
                    elif cls.startswith("Five"):
                        rating = "Five"
                        break

            # Create book instance
            book = Book(
                name=name,
                description=description,
                category=category,
                price_including_tax=price_including_tax,
                price_excluding_tax=price_excluding_tax,
                availability=availability,
                number_of_reviews=number_of_reviews,
                image_url=image_url,
                rating=rating,
                source_url=url,
                raw_html=html,
            )

            return book

        except Exception as e:
            logger.error(f"Error parsing book page {url}: {e}")
            return None

    async def _parse_catalog_page(self, html: str, base_url: str) -> list[str]:
        """Extract book URLs from catalog page.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative URLs

        Returns:
            List of book detail URLs
        """
        book_urls = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            # Find all book links
            book_links = soup.select("article.product_pod h3 a")
            for link in book_links:
                href = link.get("href", "")
                # Convert relative URL to absolute
                full_url = urljoin(base_url, href.replace("../..", ""))
                book_urls.append(full_url)
        except Exception as e:
            logger.error(f"Error parsing catalog page: {e}")
        return book_urls

    async def _get_next_page_url(self, html: str, current_url: str) -> Optional[str]:
        """Get next page URL from pagination.

        Args:
            html: HTML content
            current_url: Current page URL

        Returns:
            Next page URL or None
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            next_link = soup.select_one("li.next a")
            if next_link:
                href = next_link.get("href", "")
                return urljoin(current_url, href)
        except Exception as e:
            logger.error(f"Error finding next page: {e}")
        return None

    async def _scrape_book(self, url: str) -> Optional[Book]:
        """Scrape a single book page.

        Args:
            url: Book detail page URL

        Returns:
            Book instance or None
        """
        if url in self.crawled_urls:
            logger.debug(f"Skipping already crawled: {url}")
            return None

        response = await self._fetch_page(url)
        if not response:
            return None

        html = response.text
        book = self._parse_book_page(html, url)

        if book:
            # Save to database
            await self.storage.save_book(book, store_html=True)
            self.crawled_urls.add(url)
            logger.info(f"Scraped book: {book.name}")

        return book

    async def crawl_all(self, resume: bool = True) -> None:
        """Crawl all books from the site.

        Args:
            resume: Whether to resume from already crawled books
        """
        logger.info("Starting crawl of all books...")

        if resume:
            # Load already crawled URLs
            crawled_urls = await self.storage.get_all_book_urls()
            self.crawled_urls = set(crawled_urls)
            logger.info(f"Resuming: {len(self.crawled_urls)} books already crawled")

        # Start from catalog index
        current_catalog_url = f"{self.base_url}/index.html"
        all_book_urls: list[str] = []

        # First, collect all book URLs
        logger.info("Collecting book URLs from catalog pages...")
        while current_catalog_url:
            response = await self._fetch_page(current_catalog_url)
            if not response:
                break

            html = response.text
            book_urls = await self._parse_catalog_page(html, current_catalog_url)
            all_book_urls.extend(book_urls)
            logger.info(
                f"Found {len(book_urls)} books on page, total: {len(all_book_urls)}"
            )

            # Get next page
            current_catalog_url = await self._get_next_page_url(
                html, current_catalog_url
            )

        logger.info(f"Total books to scrape: {len(all_book_urls)}")

        # Filter out already crawled URLs if resuming
        if resume:
            new_book_urls = [
                url for url in all_book_urls if url not in self.crawled_urls
            ]
            logger.info(f"New books to scrape: {len(new_book_urls)}")
            all_book_urls = new_book_urls

        # Scrape all books concurrently
        tasks = [self._scrape_book(url) for url in all_book_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes
        success_count = sum(
            1 for r in results if r is not None and not isinstance(r, Exception)
        )
        logger.info(
            f"Crawl completed: {success_count}/{len(all_book_urls)} books scraped successfully"
        )
