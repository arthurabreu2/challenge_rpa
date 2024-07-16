# Main imports
import pandas as pd 
import datetime as dt
import logging
from utils import download_images

# RPA Imports
from RPA.Robocorp.WorkItems import WorkItems

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from robocorp.tasks import task

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@task
def extract_news():
    # Initialize WorkItems
    work_items = WorkItems()
    work_items.get_input_work_item()

    # Retrieve parameters from work items
    search_phrase = work_items.get_work_item_variable('search_phrase', 'technology')
    news_category = work_items.get_work_item_variable('news_category', 'Technology and the Internet')

    # WebDriver configuration for Firefox 
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service)
    driver.get("https://www.latimes.com")
    wait = WebDriverWait(driver, 20)

    search_icon = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-element='search-button']"))
    )
    search_icon.click()

    search_input = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[data-element='search-form-input']"))
    )
    search_input.send_keys(search_phrase)
    search_input.send_keys(Keys.ENTER)

    technology_filter = wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//span[text()='Technology and the Internet']/ancestor::label"))
    )
    technology_filter.click()

    articles = wait.until(
        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div.promo-wrapper"))
    )

    articles_list = []
    latest_date = dt.datetime(1900, 1, 1)

    for article in articles:
        try:
            title = article.find_element(By.CSS_SELECTOR, ".promo-title").text
            category = article.find_element(By.CSS_SELECTOR, ".promo-category").text
            description = article.find_element(By.CSS_SELECTOR, ".promo-description").text
            image_url = article.find_element(By.CSS_SELECTOR, "img").get_attribute('src')
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
                articles_list.append(article_data)
        except Exception as e:
            logging.error(f"Error processing in article: {str(e)}")

    if articles_list:
        # Save the latest article data excel
        df = pd.DataFrame(articles_list)
        df.to_excel('output/excel_files/news_data.xlsx', index=False)
        
        image_filename = download_images(article_data['image_url'])
        logging.info(f"Latest article from 2023 saved to Excel: {articles_list[-1]}")
    else:
        logging.info("No articles from 2023 found.")
    
    driver.quit()

    # Save output work item
    work_items.create_output_work_item({'output': 'output/excel_files/news_data.xlsx'})
