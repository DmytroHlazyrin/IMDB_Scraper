# IMDb Top 250 Movies Scraper

This project implements a web scraper to collect data from IMDb's Top 250 movies list. 
It uses the Scrapy framework for web scraping, Selenium for handling dynamic page loading, 
and the Google Sheets API for storing data in Google Sheets.

### Data Structure
You can find the scraping result at the link:
```
https://docs.google.com/spreadsheets/d/1ZPf3ispItKlziV6Y_ln9LORq8A1QYs3G1KzWYqJXv1Q/edit?usp=sharing
```
![Movies Sheet](images/movies_sheet.png)
![Actors Sheet](images/actors_sheet.png)
#### Film:
- "Position in rating",
- "Title",,
- "Original title",
- "Year",
- "Rating",
- "Director(s)" - list,
- "Cast" - list,

#### Actor:
- "Actor",
- "Movies Count",
- "Average Rating",
- "Movies" - list,

## Project Structure
- `logger.py`: Logger configuration.
- `movies/chrome_driver.py`: A class for managing an instance of Chrome WebDriver.
- `movies/google_sheets.py`: A class for interacting with Google Sheets, saving movie data, and performing actor analysis.
- `movies/spiders/top250.py`: The main scraper that gathers information about movies and actors from IMDb.

## Installation

1. Clone the repository:

```shell
git clone https://github.com/DmytroHlazyrin/IMDB_Scraper.git
cd IMDB_Scraper
```
2. Create and activate a virtual environment:

```shell
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Unix or MacOS
```

3. Install the required packages:
```shell
pip install -r requirements.txt
```

4. Configure Google Sheets integration:

    - Place your Google Sheets credentials JSON file in some directory in project.
    - Create Google Sheet
    - Set up the GOOGLE_SHEET_ID in a .env file.
    - Set up the CREDENTIALS_FILE_PATH in a .env file.

5. Install and set up ChromeDriver:
    
    - Install ChromeDriver on your computer.
    - Set up the absolute path to your ChromeDriver as CHROME_DRIVER_PATH in a .env file.

6. File handling:
    
    - Set up the path and filename for storing movies data as MOVIES_JSON_PATH in a .env file
    - Set up the path and filename for storing actors data as ACTORS_JSON_PATH in a .env file

## Running the Scraper
To run the scraper, use the following command:
```shell
scrapy crawl top250
```
Since Scrapy also has its own very detailed logging, you can run it with different logging levels:
```shell
scrapy crawl top250 -s LOG_LEVEL=INFO
```
This will start scraping the IMDb Top 250 movies and save the data to a JSON file. 
The data is then uploaded to a specified Google Sheet.

## Google Sheets Integration
The scraped data will be saved to two sheets:
- Movies Data: Contains detailed information about the Top 250 movies.
- Actor Analysis: Provides an analysis of actors based on their appearances in the Top 250 movies.

## Customization
You can adjust the range of movies to scrape by modifying the loop in the parse method inside the Top250Spider class. 
This can be useful for testing or if you only need a subset of the Top 250 movies.

## Logging
Logs are saved to top250.log in the root directory, 
providing detailed information about the scraping process and any errors encountered.

## Contact
For any inquiries or issues, please contact dmytro.hlazyrin@gmail.com