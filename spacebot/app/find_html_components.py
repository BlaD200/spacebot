from bs4 import BeautifulSoup
from requests import get


def check(url):
    html = get(url).content.decode()
    soup = BeautifulSoup(html, 'html.parser')

    td = soup.find(text='Кількість вільних місць').parent.next_sibling.next_sibling
    free_space = td.text.strip()
    if free_space != 'немає':
        return url, free_space
    else:
        return False


def find_subject_name(url):
    html = get(url).content.decode()
    soup = BeautifulSoup(html, 'html.parser')

    h1 = soup.find('div', {'class': 'page-header'}).h1
    h1.small.clear()
    name = h1.text.strip()
    if name != 'немає':
        return name
    else:
        return "Not found"

