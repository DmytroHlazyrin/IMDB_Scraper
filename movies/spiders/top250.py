import json
import scrapy
from scrapy.http import Response
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from logger import setup_logger
from ..chrome_driver import ChromeDriver


class Top250Spider(scrapy.Spider):
    name = "top250"
    allowed_domains = ["www.imdb.com"]
    start_urls = ["https://www.imdb.com/chart/top/?ref_=nv_mv_250"]

    def __init__(self, *args, **kwargs):
        super(Top250Spider, self).__init__(*args, **kwargs)
        self.driver = ChromeDriver()
        self.movies_data = []  # List to store movie data

        self.custom_logger = setup_logger(self.name, "top250.log")
        self.custom_logger.info("Processing top 250 movies")

    def close(self, reason):
        self.driver.quit()
        self.movies_data.sort(key=lambda x: x['Position in rating'])
        self.custom_logger.info("Top 250 movies processed")
        # Write movies data to JSON file
        with open('movies.json', 'w', encoding='utf-8') as f:
            json.dump(self.movies_data, f, ensure_ascii=False, indent=4)

    def parse(self, response: Response, **kwargs) -> None:
        self.driver.get(response.url)

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".ipc-metadata-list"))
        )
        movies = self.driver.find_elements(By.CSS_SELECTOR,
                                           ".ipc-metadata-list li")

        for movie in movies[245:250]:
            detail_page_url = movie.find_element(By.CSS_SELECTOR,
                                                 ".ipc-title-link-wrapper").get_attribute(
                "href")
            yield scrapy.Request(
                url=detail_page_url,
                callback=self.parse_movie_info,
                meta={'movies_data': self.movies_data}
            )

    def parse_movie_info(self, response: Response) -> None:
        try:
            self.driver.get(response.url)
            WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".sc-ec65ba05-0 > .hero__primary-text"))
            )

            self.custom_logger.info(f"Processing movie: {response.url}")

            position = self.driver.find_element(By.CSS_SELECTOR, ".sc-15ed0f38-1 > a").text.split('#')[1].strip()
            title_ukr = self.driver.find_element(By.CSS_SELECTOR,
                                                 ".sc-ec65ba05-0 > .hero__primary-text").text
            title_eng = self.driver.find_element(By.CSS_SELECTOR,
                                                 ".sc-ec65ba05-1").text.replace(
                "Original title: ", "")
            rating = response.css(".sc-eb51e184-1::text").get()
            year = self.driver.find_elements(By.CSS_SELECTOR,
                                             ".sc-ec65ba05-2 > li >.ipc-link")[
                0].text
            certification = self.driver.find_elements(By.CSS_SELECTOR,
                                                      ".sc-ec65ba05-2 > li >.ipc-link")[
                1].text
            cast_list_url = self.driver.find_element(By.CSS_SELECTOR,
                                                     ".sc-4cf2da2d-0 > li > a").get_attribute(
                "href")

            # Update meta with movie details
            response.meta.update({
                'position': int(position),
                'title_ukr': title_ukr,
                'title_eng': title_eng,
                'rating': float(rating),
                'year': int(year),
                'certification': certification
            })

            yield scrapy.Request(
                url=cast_list_url,
                callback=self.parse_cast,
                meta=response.meta
            )
        except Exception as e:
            self.custom_logger.error(f"Error processing movie: {e}")

    def parse_cast(self, response: Response) -> None:
        try:
            self.driver.get(response.url)
            WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'td.castlist_label'))
            )

            self.custom_logger.info(f"Processing cast: {response.url}")

            actors_rows = self.driver.find_elements(By.CSS_SELECTOR,
                                                    'table.cast_list tr')
            directors_rows = self.driver.find_elements(By.CSS_SELECTOR,
                                                       "#director + table > tbody > tr > .name > a")

            actors = []

            for row in actors_rows:
                label = row.find_elements(By.CSS_SELECTOR, 'td.castlist_label')
                if label and "Rest of cast listed alphabetically:" in label[
                    0].text:
                    break

                actor_name = row.find_elements(By.CSS_SELECTOR,
                                               'td:nth-child(2) a')
                if actor_name:
                    actors.append(actor_name[0].text.strip())

            directors = []

            for row in directors_rows:
                directors.append(row.text.strip())

            movie_data = {
                "Position in rating": response.meta['position'],
                "Title": response.meta['title_ukr'],
                "Original title": response.meta['title_eng'],
                "Year": response.meta['year'],
                "Rating": response.meta['rating'],
                "Certification": response.meta['certification'],
                "Director(s)": directors,
                "Cast": actors
            }

            # Add movie data to the list
            response.meta['movies_data'].append(movie_data)
        except Exception as e:
            self.custom_logger.error(f"Error processing movie: {e}")
