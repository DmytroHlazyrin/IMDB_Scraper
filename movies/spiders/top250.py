import json
import scrapy
from scrapy.http import Response
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from decouple import config

from logger import setup_logger
from ..chrome_driver import ChromeDriver
from movies.google_sheets import GoogleSheetsHandler

MOVIES_JSON_PATH = config("MOVIES_JSON_PATH")
ACTORS_JSON_PATH = config("ACTORS_JSON_PATH")

class Top250Spider(scrapy.Spider):
    """
    Spider for scraping IMDb's top 250 movies. Gathers data and stores
    it in JSON files and Google Sheets.
    """
    name = "top250"
    allowed_domains = ["www.imdb.com"]
    start_urls = ["https://www.imdb.com/chart/top/?ref_=nv_mv_250"]

    def __init__(self, *args, **kwargs):
        super(Top250Spider, self).__init__(*args, **kwargs)
        self.driver = ChromeDriver()
        self.movies_urls = []  # List to store movie URLs
        self.movies_data = []  # List to store movie data
        self.custom_logger = setup_logger(self.name, "top250.log")
        self.custom_logger.info("Processing top 250 movies")

    def close(self, reason):
        """
        Closes the WebDriver, sorts movie data, saves it to JSON, and
        uploads it to Google Sheets.
        """
        self.driver.quit()
        self.movies_data.sort(key=lambda x: x['Position in rating'])
        self.custom_logger.info("Top 250 movies processed")

        # Save data to JSON files
        with open(MOVIES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.movies_data, f, ensure_ascii=False, indent=4)

        # Process data for actor analysis
        actors = self.process_actors_analysis()
        with open(ACTORS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(actors, f, ensure_ascii=False, indent=4)

        # Upload data to Google Sheets
        creds_file = config("CREDENTIALS_FILE_PATH")
        spreadsheet_id = config("GOOGLE_SHEET_ID")
        sheets_handler = GoogleSheetsHandler(creds_file, spreadsheet_id)

        self.custom_logger.info("Uploading data to Google Sheets")
        sheets_handler.save_movies_data(MOVIES_JSON_PATH)
        sheets_handler.save_actor_analysis(ACTORS_JSON_PATH)
        self.custom_logger.info("Data uploaded successfully")

    def parse(self, response: Response, **kwargs) -> None:
        """
        Parses the main IMDb Top 250 page and collects URLs of the
        individual movie pages.
        """
        self.driver.get(response.url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".ipc-metadata-list")
            )
        )

        movies = self.driver.find_elements(
            By.CSS_SELECTOR, ".ipc-metadata-list li"
        )
        self.custom_logger.info(f"{len(movies)} movies parsed")

        for movie in movies:
            detail_page_url = movie.find_element(
                By.CSS_SELECTOR, ".ipc-title-link-wrapper"
            ).get_attribute("href")
            self.movies_urls.append(detail_page_url)

        # Trigger the batch processing of movie URLs
        for url in self.movies_urls:  # Adjust the range as needed
            yield scrapy.Request(
                url=url,
                callback=self.parse_movie_info
            )

    def parse_movie_info(self, response: Response) -> None:
        """
        Parses individual movie pages and extracts detailed information.
        """
        try:
            self.driver.get(response.url)
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".sc-ec65ba05-0 > .hero__primary-text")
                )
            )

            position = self.driver.find_element(
                By.CSS_SELECTOR, ".sc-15ed0f38-1 > a"
            ).text.split('#')[1].strip()

            title = self.driver.find_element(
                By.CSS_SELECTOR, ".sc-ec65ba05-0 > .hero__primary-text"
            ).text

            try:
                orig_title = self.driver.find_element(
                    By.CSS_SELECTOR, ".sc-ec65ba05-1"
                ).text.replace("Original title: ", "")

            except Exception:
                self.custom_logger.warning(
                    f"Error retrieving original title for movie: {title}")
                orig_title = title

            rating = response.css(".sc-eb51e184-1::text").get()

            year = self.driver.find_elements(
                By.CSS_SELECTOR, ".sc-ec65ba05-2 > li >.ipc-link"
            )[0].text

            cast_list_url = self.driver.find_element(
                By.CSS_SELECTOR, ".sc-4cf2da2d-0 > li > a"
            ).get_attribute("href")

            self.custom_logger.info(
                f"Processing movie: {position} - {orig_title}"
            )

            yield scrapy.Request(
                url=cast_list_url,
                callback=self.parse_cast,
                meta={
                    'position': int(position),
                    'title': title,
                    'orig_title': orig_title,
                    'rating': float(rating),
                    'year': int(year),
                }
            )

        except TimeoutException as e:
            self.custom_logger.warning(
                f"Timeout while waiting for movie on {response.url}: {e}")
        except Exception as e:
            self.custom_logger.error(f"Error processing movie: {e}")

    def parse_cast(self, response: Response) -> None:
        """
        Parses the cast list of a movie and extracts actor and director
        information.
        """
        try:
            self.driver.get(response.url)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'td.castlist_label')
                )
            )

            self.custom_logger.info(
                f"Processing cast: {response.meta['position']} - "
                f"{response.meta['orig_title']}"
            )

            actors_rows = self.driver.find_elements(
                By.CSS_SELECTOR, 'table.cast_list tr'
            )
            directors_rows = self.driver.find_elements(
                By.CSS_SELECTOR, "#director + table > tbody > tr > .name > a"
            )

            actors = []

            for row in actors_rows:
                label = row.find_elements(By.CSS_SELECTOR, 'td.castlist_label')
                if (
                        label and
                        "Rest of cast listed alphabetically:" in label[0].text
                ):
                    break
                actor_name = row.find_elements(
                    By.CSS_SELECTOR, 'td:nth-child(2) a'
                )
                if actor_name:
                    actors.append(actor_name[0].text.strip())

            directors = [row.text.strip() for row in directors_rows]

            movie_data = {
                "Position in rating": response.meta['position'],
                "Title": response.meta['title'],
                "Original title": response.meta['orig_title'],
                "Year": response.meta['year'],
                "Rating": response.meta['rating'],
                "Director(s)": directors,
                "Cast": actors
            }

            self.movies_data.append(movie_data)

        except TimeoutException as e:
            self.custom_logger.warning(
                f"Timeout while waiting for cast on {response.url}: {e}")
        except Exception as e:
            self.custom_logger.error(f"Error processing cast: {e}")

    def process_actors_analysis(self):
        """
        Processes the collected movie data to analyze actor appearances
        and average ratings.
        """
        actor_counts = {}
        for movie in self.movies_data:
            for actor in movie.get("Cast", []):
                if actor not in actor_counts:
                    actor_counts[actor] = {
                        "Movies Count": 0,
                        "Total Rating": 0,
                        "Movies": []
                    }
                actor_counts[actor]["Movies Count"] += 1
                actor_counts[actor]["Total Rating"] += movie.get("Rating", 0)
                actor_counts[actor]["Movies"].append(movie["Original title"])

        # Calculate average rating for each actor
        actors_analysis = []
        for actor, data in actor_counts.items():
            if data["Movies Count"] > 1:  # Exclude actors with only one movie
                average_rating = round(
                    data["Total Rating"] / data["Movies Count"], 2
                )
                actors_analysis.append({
                    "Actor": actor,
                    "Movies Count": data["Movies Count"],
                    "Average Rating": average_rating,
                    "Movies": data["Movies"]
                })

        return actors_analysis
