import requests
from bs4 import BeautifulSoup
def scrape(url):
    res = requests.get(url)
    return BeautifulSoup(res.text, 'html.parser').title.text
