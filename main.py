from airflow import DAG
from airflow.operators.python import PythonOperator


from datetime import datetime
import pandas as pd
import json
from bs4 import BeautifulSoup
import requests

def scrape_news():
    
    url = 'https://www.dawn.com/'
    response = requests.get(url)
    
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        articles = []
        
        for article_tag in soup.find_all('article', class_='story'):
            title_tag = article_tag.find('h2')
            link_tag = article_tag.find('a', href=True)
            
            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                print(title)
                link = link_tag['href']
                articles.append({'title': title, 'link': link})
        
        with open('dawn_articles.json', 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=4)
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

def transform_data():
    news_data = pd.read_json("dawn_articles.json").to_dict(orient="records")
    
    for index,a in enumerate(news_data):
        topic=a['link'].split('/')[-1]
        news_data[index]['topic']=topic
        news_data[index].pop('link')
    
    print(news_data)


dag = DAG(
    'News_DAG',
    schedule_interval='@daily', 
    start_date=datetime(2024, 11, 16),  
    catchup=False, 
)

task_1 = PythonOperator(
    task_id='extract_data', 
    python_callable=scrape_news,   
    dag=dag, 
)

task_2 = PythonOperator(
    task_id='load_to_mongo', 
    python_callable=transform_data,   
    dag=dag,  #
)

task_1 >> task_2
