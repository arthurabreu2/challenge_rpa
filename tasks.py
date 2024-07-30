# RPA imports
from robocorp.tasks import task
from RPA.Robocorp.WorkItems import WorkItems
from rpa_challenge import FreshNews

import logging

# Selenium imports
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# RPA Task to extract news 
@task
def extract_news():
    """
    Main task to initialize and control the news scraping process. 
    """
    work_items = WorkItems()    
    scraper = None
    try:
        work_items.get_input_work_item()
        search_phrase = work_items.get_work_item_variable('search_phrase', 'technology')
        news_category = work_items.get_work_item_variable('news_category', 'Technology and the Internet')
        
        scraper = FreshNews(search_phrase, news_category)
        try:
            scraper.search_articles()
            scraper.extract_data()
            scraper.save_data()
        except (TimeoutException, NoSuchElementException, WebDriverException) as e:
            logging.error(f"An error occurred during the scraping process: {e}")
        finally:
            scraper.close_driver()
    except (KeyError, ValueError) as e:
        logging.error(f"Failed to retrieve or process work items: {e}")
    finally:
        if scraper:
            scraper.close_driver()
        if work_items:
            # Assumes create_output_work_item processes the outcome of the scraping, potentially for further steps.
            try:
                work_items.create_output_work_item({'output': 'output/excel_files/news_data.xlsx'})
            except (KeyError, ValueError) as e:
                logging.error(f"Failed to create output work item: {e}")