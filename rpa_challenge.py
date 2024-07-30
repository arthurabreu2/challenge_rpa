# Main imports
import pandas as pd
import datetime as dt
import logging

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

# Utils
from utils import download_images

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FreshNews:
    """
    A class to scrape news articles from the 'Los Angeles Times' website based on specified search criteria.
    
    Attributes:
        search_phrase (str): The search phrase to filter articles.
        news_category (str): The category within which to filter articles.
        driver (webdriver): Instance of a Firefox WebDriver to navigate and scrape the website.
        articles_list (list): List to store extracted data from each article.
    """

    def __init__(self, search_phrase, news_category):
        """
        Initializes the NewsScraper with the necessary search parameters and sets up the WebDriver.
        
        Parameters:
            search_phrase (str): The search term to use in the article search.
            news_category (str): The news category to further filter the search results.
        """
        self.search_phrase = search_phrase
        self.news_category = news_category
        self.driver = self.configure_driver()
        self.articles_list = []
        
    def configure_driver(self):
        """
        Configures and initializes the Firefox WebDriver with necessary settings.
        
        Returns:
            webdriver.Firefox: A configured instance of Firefox WebDriver.
        
        Raises:
            WebDriverException: An error occurred while setting up the WebDriver.
        """
        try:
            options = Options()
            options.add_argument("--headless")  
            options.add_argument("--no-sandbox")  
            options.add_argument("--disable-dev-shm-usage")  

            driver = webdriver.Chrome(options=options)
            driver.get("https://www.latimes.com")
            return driver
        except WebDriverException as e:
            logging.error(f"Failed to configure the WebDriver: {e}")
            raise
    
    def search_articles(self):
        """
        Navigates through the website and sets the filters based on the initialized search parameters.
        
        Raises:
            TimeoutException: If the page elements do not become available within the timeout period.
            NoSuchElementException: If the search elements are not found on the page.
        """
        try:
            wait = WebDriverWait(self.driver, 20)
            search_icon = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-element='search-button']")))
            search_icon.click()

            search_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[data-element='search-form-input']")))
            search_input.send_keys(self.search_phrase)
            search_input.send_keys(Keys.ENTER)

            technology_filter = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@data-name='Topics']//span[contains(text(), '" + self.news_category + "')]"))
            )
            technology_filter.click()

        except TimeoutException as e:
            logging.error(f"Timeout occurred while searching articles: {e}")
            raise
        except NoSuchElementException as e:
            logging.error(f"Element not found during search setup: {e}")
            raise
    
    def extract_data(self):
        """
        Extracts relevant data from each article found after setting filters and stores it in a list.
        
        Each article's data includes title, category, description, publication date, and image URL.
        
        Raises:
            TimeoutException: If the articles do not become visible within the timeout period.
            NoSuchElementException: If required elements are not found in the articles.
        """
        try:
            articles = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_all_elements_located((By.XPATH, "//div[contains(@class, 'promo-wrapper')]"))
            )
            latest_date = dt.datetime(1900, 1, 1)
            for article in articles:
                try:
                    image_element = WebDriverWait(article, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "img"))
                    )
                    image_url = image_element.get_attribute('src')
                    if not image_url:
                        image_url = article.find_element(By.XPATH, "picture/source[1]").get_attribute('srcset').split()[0]
                except NoSuchElementException:
                    logging.warning("Image not found for one of the articles, skipping...")
                    pass
                except TimeoutException:
                    logging.warning("Timed out waiting for the image to become visible.")
                    pass
                
                title = article.find_element(By.CSS_SELECTOR, ".promo-title").text
                category = article.find_element(By.XPATH, "//*[contains(@class, 'promo-category')]").text
                description = article.find_element(By.CSS_SELECTOR, ".promo-description").text
                date_str = article.find_element(By.CSS_SELECTOR, ".promo-timestamp").get_attribute('data-timestamp')
                date_article = dt.datetime.fromtimestamp(int(date_str)/1000)
                if date_article.year == 2023 and date_article > latest_date:
                    latest_date = date_article
                    article_data = {
                        'title': title,
                        'category': category,
                        'description': description,
                        'date': date_article.strftime('%Y-%m-%d'),
                        'image_url': image_url
                    }
                    self.articles_list.append(article_data)
                    print(article_data)
        except TimeoutException as e:
            logging.error(f"Timeout during data extraction: {e}")
            raise
        except NoSuchElementException as e:
            logging.error(f"Element not found during data extraction: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during data extraction: {e}")
            raise

    def save_data(self):
        """
        Saves the extracted articles data to an Excel file, if any articles were found.
        
        Uses the latest article's image for downloading and logging.
        """
        try:
            if self.articles_list:
                df = pd.DataFrame(self.articles_list)
                df.to_excel('output/excel_files/news_data.xlsx', index=False)
                logging.info("Data saved to Excel.")
                download_images(self.articles_list[-1]['image_url'])
            else:
                logging.info("No articles found.")
        except NoSuchElementException as e:
            logging.error(f"An error occurred while saving data: {e}")
            raise

    def close_driver(self):
        """
        Safely closes the WebDriver session to free up resources.
        """
        try:
            self.driver.quit()
        except WebDriverException as e:
            logging.error(f"An error occurred while closing the WebDriver: {e}")
