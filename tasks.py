import pandas as pd 
import datetime as dt
import logging
from utils import download_images
from RPA.Robocorp.WorkItems import WorkItems
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from robocorp.tasks import task

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
@task
def extract_news():
    try:
        # Initialize WorkItems
        work_items = WorkItems()
        work_items.get_input_work_item()

        # Retrieve parameters from work items
        search_phrase = work_items.get_work_item_variable('search_phrase', 'technology')
        news_category = work_items.get_work_item_variable('news_category', 'Technology and the Internet')

        logging.info(f"Search Phrase: {search_phrase}")
        logging.info(f"News Category: {news_category}")

        # WebDriver configuration for Chrome
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=service, options=options)
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
            EC.element_to_be_clickable((By.XPATH, f"//span[text()='{news_category}']/ancestor::label"))
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
                logging.error(f"Error processing article: {str(e)}")

        if articles_list:
            # Save the latest article data to Excel
            df = pd.DataFrame(articles_list)
            df.to_excel('output/excel_files/news_data.xlsx', index=False)
            
            image_filename = download_images(article_data['image_url'])
            logging.info(f"Latest article from 2023 saved to Excel: {articles_list[-1]}")
        else:
            logging.info("No articles from 2023 found.")
        
        # Save output work item
        output_item = work_items.create_output_work_item()
        output_item["output"] = 'output/excel_files/news_data.xlsx'
        work_items.release_output_work_item()
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    extract_news()