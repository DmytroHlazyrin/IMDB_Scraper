from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from decouple import config


class ChromeDriver:
    """
    Singleton class to manage Chrome WebDriver instance.
    Ensures only one instance of the WebDriver is created.
    """
    _instance = None
    chrome_driver_path = config("CHROME_DRIVER_PATH")
    service = Service(chrome_driver_path)

    def __new__(cls) -> webdriver:
        """
        Creates and returns a single instance of the Chrome WebDriver.
        """
        if cls._instance is None:
            cls._instance = super(ChromeDriver, cls).__new__(cls)
            cls._instance.driver = webdriver.Chrome(service=cls.service)
        return cls._instance.driver

    def __enter__(self) -> webdriver:
        """
        Context manager entry method. Returns the WebDriver instance.
        """
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit method. Quits the WebDriver instance.
        """
        self.driver.quit()
