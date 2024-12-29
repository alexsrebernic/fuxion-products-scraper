import requests
from bs4 import BeautifulSoup

# Function to scrape product data
def scrape_products(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
    }
    
    try:
        # Send a GET request to the URL
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for request errors

        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # List to store product data
        products = []

        # Find all product containers
        for product in soup.find_all('div', class_='content-item shop-product'):
            try:
                # Extract product name
                name = product.find('div', class_='nameProduct').text.strip()

                # Extract product price
                price = product.find('span', class_='price').text.strip()

                # Extract product points
                points = product.find('input', class_='pointProduct')['value']

                # Extract image URL
                image_url = product.find('img', class_='product-image')['src']

                # Create a dictionary for the product data
                product_data = {
                    "name": name,
                    "price": price,
                    "points": points,
                    "image_url": image_url
                }
                products.append(product_data)
            except AttributeError as e:
                print(f"Error parsing a product entry: {e}")
        
        return products

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []

# URL of the product page
url = "https://ifuxion.com/alexsrebernic/enrollment/products"

# Scrape the product data
products = scrape_products(url)

# Print the product data
for p in products:
    print(f"Name: {p['name']}\nPrice: {p['price']}\nPoints: {p['points']}\nImage URL: {p['image_url']}\n{'-'*40}")
