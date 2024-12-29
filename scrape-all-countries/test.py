from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import os
import logging
import time
import sys
import threading
import itertools

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LoadingSpinner:
    def __init__(self, desc="Loading"):
        self.desc = desc
        self.spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.running = False
        self.spinner_thread = None

    def spin(self):
        while self.running:
            sys.stdout.write(f"\r{next(self.spinner)} {self.desc}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write(f"\r✓ {self.desc}\n")
        sys.stdout.flush()

    def __enter__(self):
        self.running = True
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join()

def load_country_names():
    try:
        with open('./helpers/country-codes-to-country-names.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading country names: {e}")
        return {}

def setup_selenium():
    with LoadingSpinner("Setting up browser..."):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Clear cookies
        options.add_argument('--disable-cookies')
        
        driver = webdriver.Chrome(options=options)
        return driver

def get_all_countries(driver):
    try:
        with LoadingSpinner("Fetching available countries..."):
            driver.get("https://ifuxion.com/alexsrebernic/enrollment/products")
            
            # Delete any existing cookies
            driver.delete_all_cookies()
            
            dropdown_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".box-icon-header-3 img.pointer"))
            )
            dropdown_button.click()

            country_elements = driver.find_elements(By.CSS_SELECTOR, ".box-items-menu-logged img")
            country_codes = [elem.get_attribute("data-role") for elem in country_elements]
            
            # Add Argentina if not present
            if 'AR' not in country_codes:
                country_codes.append('AR')
                logger.info("Added Argentina (AR) to available countries")
            
            # Sort countries alphabetically
            country_codes.sort()
            
            return country_codes
    except Exception as e:
        logger.error(f"Error extracting country codes: {e}")
        return []
    
def select_countries(country_codes, country_names):
    print("\nAvailable countries:")
    available_countries = []
    
    for i, code in enumerate(country_codes, 1):
        name = country_names.get(code, "Unknown Country")
        available_countries.append((code, name))
        print(f"{i}. {name} ({code})")
    
    while True:
        try:
            selection = input("\nEnter the numbers of countries you want to scrape (comma-separated) or 'all' for all countries: ").strip()
            
            if selection.lower() == 'all':
                return country_codes
            
            selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_countries = []
            
            for idx in selected_indices:
                if 0 <= idx < len(country_codes):
                    selected_countries.append(country_codes[idx])
                else:
                    print(f"Invalid selection: {idx + 1}")
                    continue
            
            if selected_countries:
                return selected_countries
            print("Please select at least one valid country.")
            
        except ValueError:
            print("Please enter valid numbers separated by commas or 'all'")
            
def select_country(driver, country_code):
    try:
        # For Argentina, handle the special case
        if country_code == 'AR':
            # Delete existing cookies
            driver.delete_all_cookies()
            
            # Add Argentina cookie (you might need to adjust these values based on the actual cookie structure)
            cookie = {
                'name': 'selected_country',
                'value': 'AR',
                'domain': '.ifuxion.com'
            }
            driver.add_cookie(cookie)
            
            # Refresh the page to apply the cookie
            driver.refresh()
            return

        # Normal country selection for other countries
        dropdown_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".box-icon-header-3 img.pointer"))
        )
        dropdown_button.click()

        country_img = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"img[data-role='{country_code}']"))
        )
        country_img.click()

        time.sleep(2)
    except Exception as e:
        logger.error(f"Error selecting country {country_code}: {e}")
        raise

def scrape_products(driver, url, country_code):
    try:
        with LoadingSpinner(f"Scraping products..."):
            driver.get(url)
            select_country(driver, country_code)
            
            products = []
            page = 1

            while True:
                soup = BeautifulSoup(driver.page_source, "html.parser")
                products.extend(scrape_product_page(driver, soup, country_code))

                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)

                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.jp-next:not(.jp-disabled)'))
                    )
                    next_button.click()
                    time.sleep(3)
                    page += 1

                except Exception as e:
                    break

            return products

    except Exception as e:
        logger.error(f"Request error for {country_code}: {e}")
        return []


def scrape_product_page(driver, soup, country_code):
    try:
        products = []

        for product in soup.find_all('div', class_='content-item shop-product'):
            try:
                name_tag = product.find('div', class_='nameProduct')
                name = name_tag.text.strip() if name_tag else "No Name"

                price_tag = product.find('span', class_='price')
                price = price_tag.text.strip() if price_tag else "No Price"

                points_tag = product.find('input', class_='pointProduct')
                points = points_tag['value'] if points_tag else "No Points"

                image_tag = product.find('img', class_='product-image')
                image_url = image_tag['src'] if image_tag else "No Image URL"

                detail_url_tag = product.find('a', class_='hovMoreInfo')
                detail_url = "https://ifuxion.com" + detail_url_tag['href'] if detail_url_tag else "No Detail URL"

                detail_data = scrape_product_details(driver, detail_url) if detail_url_tag else {}

                product_data = {
                    "name": name,
                    "price": price,
                    "points": points,
                    "image_url": image_url,
                    "detail_url": detail_url,
                    **detail_data
                }
                products.append(product_data)
            except AttributeError as e:
                logger.error(f"Error parsing a product entry for {country_code}: {e}")

        return products

    except Exception as e:
        logger.error(f"Error scraping product page for {country_code}: {e}")
        return []

def scrape_product_details(driver, detail_url):
    try:
        driver.get(detail_url)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract SKU
        sku_tag = soup.find('div', class_='itemcode')
        sku = sku_tag.text.strip().replace("SKU:", "").strip() if sku_tag else "No SKU"

        # Extract description
        description = extract_description(soup)

        # Extract benefits
        benefits = extract_tab_content(soup, 'caja_1', 'Beneficios')

        # Extract usage suggestion
        usage_suggestion = extract_tab_content(soup, 'caja_2', 'Sugerencia de uso')

        # Extract additional images
        additional_images = extract_images(soup)

        detail_data = {
            "sku": sku,
            "description": description,
            "benefits": benefits,
            "usage_suggestion": usage_suggestion,
            "additional_images": additional_images
        }

        return detail_data

    except Exception as e:
        logger.error(f"Request error for detail page: {e}")
        return {}

def extract_description(soup):
    # Extracting the description depending on the page structure
    descrp = soup.find('div', class_='detalleProductoDescripcion')
    return descrp.get_text(strip=True) if descrp else "No Description"

def extract_tab_content(soup, tab_id, default_title):
    tab_content = soup.find('div', id=tab_id)
    if tab_content:
        title_tag = tab_content.find('h4', class_='colorTheme')
        title = title_tag.get_text(strip=True) if title_tag else default_title
        content = tab_content.get_text(strip=True)
        return f"{title}: {content}"
    return "No Information"

def extract_images(soup):
    images = []
    image_tags = soup.select('.carousel-inner .thumbnail img')
    for img_tag in image_tags:
        img_url = img_tag['src'] if 'src' in img_tag.attrs else None
        if img_url:
            images.append(img_url)
    
    return images

def save_products_to_json(products, country_code):
    folder_name = "country_products"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    file_path = os.path.join(folder_name, f"{country_code}_products.json")
    with LoadingSpinner(f"Saving data for {country_code}..."):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
    
    logger.info(f"Products for {country_code} saved to {file_path}")


def main():
    try:
        base_url = "https://ifuxion.com/alexsrebernic/enrollment/products"
        
        with LoadingSpinner("Loading country names from file..."):
            country_names = load_country_names()
            time.sleep(1)  # Adding a small delay to make the loading visible
        
        driver = setup_selenium()
        country_codes = get_all_countries(driver)

        if not country_codes:
            logger.error("No countries found. Exiting.")
            return

        selected_country_codes = select_countries(country_codes, country_names)
        
        if not selected_country_codes:
            logger.error("No countries selected. Exiting.")
            return

        selected_names = [f"{country_names.get(code, 'Unknown')} ({code})" for code in selected_country_codes]
        logger.info(f"Starting scraping for selected countries: {', '.join(selected_names)}")

        for country_code in selected_country_codes:
            country_name = country_names.get(country_code, "Unknown Country")
            logger.info(f"Processing {country_name} ({country_code})...")
            products = scrape_products(driver, base_url, country_code)
            
            if products:
                save_products_to_json(products, country_code)
                logger.info(f"Finished scraping for {country_name} ({country_code})")
            else:
                logger.warning(f"No products scraped for {country_name} ({country_code})")
            
            logger.info("-" * 40)

        driver.quit()
        logger.info("Scraping completed for selected countries.")

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
