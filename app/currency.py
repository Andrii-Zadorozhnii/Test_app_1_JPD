import logging

import requests
from bs4 import BeautifulSoup

from app.models import Expense


def get_usd_exchange_rate()->float:
    try:
        url = 'https://minfin.com.ua/currency/nbu/'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        rate_div = soup.find('td', text='Доллар США').find_next('td').find_next('div').text.strip()[:5]
        return float(rate_div.replace(',','.'))
    except requests.exceptions.RequestException as e:
        logging.error(f'Error: {e}')
