import csv
import json
import time
import requests
from bs4 import BeautifulSoup
import os

input_file = "data/breeds 1.csv"
output_file = "data/breed_descriptions.json"

def scrape():
    if not os.path.exists(input_file):
        print(f"{input_file} not found.")
        return

    descriptions = {}
    
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                descriptions = json.load(f)
            except:
                pass

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        count = 0
        for row in reader:
            if not row or len(row) < 2:
                continue
            breed = row[0].strip()
            url = row[1].strip()
            key = breed.lower()
            
            if key in descriptions and descriptions[key] != "Description not available.":
                continue
                
            print(f"Scraping {breed}...")
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                }
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    desc = ""
                    for p in soup.find_all('p'):
                        text = p.get_text(strip=True)
                        if len(text.split()) > 15 and "advertisement" not in text.lower():
                            desc = text
                            break
                    if desc:
                        descriptions[key] = desc
                    else:
                        descriptions[key] = "Description not available."
                else:
                    descriptions[key] = "Description not available."
            except Exception as e:
                print(f"Error {breed}: {e}")
                descriptions[key] = "Description not available."
                
            count += 1
            if count % 20 == 0:
                with open(output_file, 'w', encoding='utf-8') as out:
                    json.dump(descriptions, out, ensure_ascii=False, indent=2)
                
            time.sleep(0.1) # Fast scraping
            
    with open(output_file, 'w', encoding='utf-8') as out:
        json.dump(descriptions, out, ensure_ascii=False, indent=2)
    print("Done scraping!")

if __name__ == "__main__":
    scrape()
