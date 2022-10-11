from fastapi import FastAPI
from google.cloud import bigquery
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from hubspot.crm.companies import SimplePublicObjectInput, ApiException
import hubspot

from selenium import webdriver
from selenium.webdriver.common.by import By
import chromedriver_binary  # Adds chromedriver binary to path

from datetime import date

#### Scrapping data

links = {'newyork':'https://culinaryagents.com/search/jobs?search%5Bcountry%5D=US&search%5Blocation%5D=New+York%2C+NY',
         'atlanta':'https://culinaryagents.com/search/jobs?search%5Blocation%5D=Atlanta%2C%20GA',
         'chicago':'https://culinaryagents.com/search/jobs?search[location]=Chicago,%20IL',
         'losangeles':'https://culinaryagents.com/search/jobs?search[location]=Los%20Angeles,%20CA',
         'dallas':'https://culinaryagents.com/search/jobs?search[location]=Dallas,%20TX'}

city_state = {'newyork':['New York','NY'],
         'atlanta':['Atlanta', 'GA'],
         'chicago': ['Chicago', 'IL'],
         'losangeles': ['Los Angeles', 'CA'],
         'dallas':['Dallas', 'TX']}



def get_info(card):
    
    clean = {}
    job_title = card.find_all(attrs={'class':'job-title text-ellipsis text-primary'})[0].text
    company_and_address = card.find_all(attrs={'class':'text-muted text-ellipsis'})
    
    if (len(company_and_address) == 2):
        company = company_and_address[0].text
        address = company_and_address[1].text

        clean = {
                 'company': company,
                 'job_title' : job_title,
                 'date' : date.today(),
                 'address' : address
        }
    
    return(clean)

def parse_page(soup):
    cards = soup.find_all(attrs={'class':'key-info'})
    
    cards_info = [get_info(card) for card in cards]
    
    cards_info  = pd.DataFrame(cards_info)
    
    
    return cards_info 


def data_from_city(city, links = links, city_state = city_state ):
    if city in links.keys():

        link = links[city]
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("window-size=1024,768")
        chrome_options.add_argument("--no-sandbox")

        # Initialize a new browser
        driver = webdriver.Chrome(chrome_options=chrome_options)


        driver.get(link)

        time.sleep(5)

        if False:
            load_more = driver.find_element( By.XPATH,'''//*[@id="load_more_btn"]''')
            load_more.click()
            time.sleep(5)


            load_more = driver.find_element( By.XPATH,'''//*[@id="load_more_btn"]''')
            load_more.click()
            time.sleep(5)

            load_more = driver.find_element( By.XPATH,'''//*[@id="load_more_btn"]''')
            load_more.click()
            time.sleep(5)


        html_source = driver.page_source

        soup = BeautifulSoup(html_source, 'html.parser')


        ans = parse_page(soup)

        client = bigquery.Client()

        table_id = "landed-big-query.analytics.culinary_agents_job_posting"


        to_upload = ans.dropna()

        to_upload['city'] = city_state[city][0]
        to_upload['state'] = city_state[city][1]

        logging.warning('uploading {} rows'.format(len(to_upload)))

        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
        )


        job = client.load_table_from_dataframe(
            to_upload, table_id, job_config=job_config
        )  # Make an API request.
        job.result()  # Wait for the job to complete.

    else:
        return {"message": "City not configured"}


def create_company(company, address, city, state):
    client = hubspot.Client.create(access_token=os.environ['hs_token'] )
    properties = {
        "city": city,
        "name": company,
        "state": state,
        'source': 'Culinary Agents Scrape Lead',
        'hubspot_owner_id': '233756268',
        'address':address,
        'country':'United States'
    }
    
    simple_public_object_input = SimplePublicObjectInput(properties=properties)
    try:
        api_response = client.crm.companies.basic_api.create(simple_public_object_input=simple_public_object_input)
    except ApiException as e:
        print("Exception when calling basic_api->create: %s\n" % e)
        
    return 'done'


def update_hs(n=5):

    sql = '''SELECT distinct t1.company,t1.address, t1.city, t1.state
    FROM `landed-big-query.analytics.culinary_agents_job_posting` t1
    LEFT JOIN `landed-big-query.analytics.culinary_agents_created_companies` t2 using (company,address)
    WHERE t2.company IS NULL'''


    client = bigquery.Client()

    companies_to_upload = client.query(sql).result().to_dataframe()
    
    if (n>0):
        mini = companies_to_upload.head(n)
    else:
        mini = companies_to_upload


    for _, row in mini.iterrows():  
        
        company = row['company']
        address = row['address']
        city = row['city']
        state = row['state']
        print(company)
        create_company(company, address, city, state)


    to_upload = mini[['company','address']]


    table_id = "landed-big-query.analytics.culinary_agents_created_companies"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
    )


    job = client.load_table_from_dataframe(
        to_upload, table_id, job_config=job_config
    )  # Make an API request.
    job.result()  # Wait for the job to complete.





app = FastAPI()


@app.get("/upload_city")
async def upload_city(city):
    logging.warning(city)
    if city in links.keys():
        data_from_city(city)
        return {"message": "Updated!"}
    else:
        return {"message": "City not configured"}



@app.get("/create_companies")
async def create_companies(n):
    n = int(n)
    logging.warning(n) 
    update_hs(n=n)
    return {"message": "Updated!"}
    
