from bs4 import BeautifulSoup
import requests as req
import json

searchtext = "Iron"
url = "https://www.tradeindia.com/search.html?loggedin_sellers=0&loggedin_profiles_list=0&keyword={}&search_form_id=18&list_type=search&paginate=1&page_no={}&_=1659683889285".format("%20".join(searchtext.split()),1)
soup = BeautifulSoup(req.get(url).content,features="html.parser")
cards = soup.find_all('div', class_='card d-flex flex-column justify-content-between')

# loop through each card and extract the required information
for card in cards:
    # extract the title/name
    try:
        title = card.find('h2', class_='Typography__Body1R-sc-gkds4f-11 NaAjH mb-1 card_title Body3R').text
    except:
        title = ""
        
    # extract the image URL
    try: img_url = card.find('img', alt=title)['src']
    except: img_url = ""
    
    # extract the price
    try:price = card.find('p', class_='Typography__Body2R-sc-gkds4f-12 erHNQZ Body3R').text
    except: price = 0
    # extract the manufacturer name
    try:manufacturer = card.find('h3', class_='Typography__Body2R-sc-gkds4f-12 btRVFt mt-2 Body4R coy-name').text
    except: manufacturer = ""
    # extract the address
    try:address = card.find('span', class_='Typography__Body2R-sc-gkds4f-12 cxqrye mb-1 Body4R')['title']
    except: address = ''
    # print the extracted information
    print('Title/Name:', title)
    print('Image URL:', img_url)
    print('Price:', price)
    print('Manufacturer Name:', manufacturer)
    print('Address:', address)
    print('\n')