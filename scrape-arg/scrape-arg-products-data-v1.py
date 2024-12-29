import requests
from bs4 import BeautifulSoup

def scrape_products(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
    }
    
    cookies = {
        "aa260671-1d96-4227-8246-83e763579f43": "2093534|1|AR",
        "FuXionCountry": "AR",
        "FuXionSiteCulture": "es-AR",
        "FuxionEnrollmentCart": "f0687783-b392-4179-9a78-b8fedacf581f",
        "FuxionEnrollmentPropertyBag": "ca0e50da-91cd-4e50-8777-cb4edd805ae1",
        "FuxionLanguage": "es-MX",
        "Fuxion_LastWebAlias": "alexsrebernic",
        "__RequestVerificationToken": "mmbjz9CqJufgUfYxeDlexlQSYMt-7I-WxWY9Ofd4_a91B5apNmp6OSLLnnSmokFXqA0TPxLmKm6ntBMbRbSVdxTWrH41",
        "_ga": "GA1.2.718777076.1725291860",
        "_ga_6NW5CRQYLT": "GS1.2.1725287187.3.1.1725291958.37.0.0",
        "_gid": "GA1.2.177875633.1725291860",
        "ai_session": "eQYt+|1725287214965|1725291958608",
        "ai_user": "D1G3m|2024-09-02T15:44:19.852Z",
        "getToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6IkZ1eGlvblRlc3QiLCJyb2xlIjoiQWRtaW4iLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3ZlcnNpb24iOiJWMSIsIm5iZiI6MTcyNTI5MTg1NiwiZXhwIjoyMDQwODI0NjU2LCJpYXQiOjE3MjUyOTE4NTZ9.RGR7QYECrUTezPikT4GsdFQd_-vEm-rjAlOrJyhll4E",
        "threadCode": "BXH799AjrtjRNbYpkf9R"
    }

    try:
        session = requests.Session()
        session.headers.update(headers)
        session.cookies.update(cookies)

        # Simulate local storage
        session.headers.update({
            "AR": "",
            "ai_session": "eQYt+|1725287214965|1725291953575.6",
            "CategoryIDGaleon": "",
            "CategoryIDLussome": "",
            "loglevel": "INFO"
        })

        response = session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

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

                detail_data = scrape_product_details(session, detail_url) if detail_url_tag else {}

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
                print(f"Error parsing a product entry: {e}")
        
        return products

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []

def scrape_product_details(session, detail_url):
    try:
        response = session.get(detail_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        sku_tag = soup.find('div', class_='itemcode')
        sku = sku_tag.text.strip().replace("SKU:", "").strip() if sku_tag else "No SKU"

        description_tags = soup.find_all('div', class_='detalleProductoDescripcion')
        description = " ".join([tag.get_text(strip=True) for tag in description_tags])
        description = description if description else "No Description"

        benefits_tag = soup.find('div', id='caja_1')
        benefits = benefits_tag.get_text(strip=True) if benefits_tag else "No Benefits"

        usage_suggestion_tag = soup.find('div', id='caja_2')
        usage_suggestion = usage_suggestion_tag.get_text(strip=True) if usage_suggestion_tag else "No Usage Suggestion"

        image_tags = soup.select('.carousel-inner .thumbnail')
        additional_images = [tag['data-image'] for tag in image_tags if 'data-image' in tag.attrs]

        detail_data = {
            "sku": sku,
            "description": description,
            "benefits": benefits,
            "usage_suggestion": usage_suggestion,
            "additional_images": additional_images
        }

        return detail_data

    except requests.exceptions.RequestException as e:
        print(f"Request error for detail page: {e}")
        return {}

url = "https://ifuxion.com/alexsrebernic/enrollment/products"

products = scrape_products(url)

for p in products:
    print(f"Name: {p['name']}\nPrice: {p['price']}\nPoints: {p['points']}\nSKU: {p.get('sku')}\nDescription: {p.get('description')}\nBenefits: {p.get('benefits')}\nUsage Suggestion: {p.get('usage_suggestion')}\nImage URL: {p['image_url']}\nAdditional Images: {p.get('additional_images')}\nDetail URL: {p['detail_url']}\n{'-'*40}")