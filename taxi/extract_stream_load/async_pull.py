import warnings
import asyncio
import aiohttp
import backoff
import requests
from datetime import datetime
import re
import time
import pandas as pd
import random
import math
from taxi_producer import TaxiProducer

async def fetch_data(session, url, params):
    async with session.get(url, params = params) as response:
        return await response.json()

@backoff.on_exception(backoff.expo, (aiohttp.ClientError, asyncio.TimeoutError), max_tries=1)
async def fetch_page(session, page_size, page_num):
    params = {
        '$limit': page_size,
        '$offset': page_num * page_size,
        '$$app_token': '9OBjTz7cstV0QIa0gQg3aNrEs'
    }
    url = 'https://data.cityofchicago.org/resource/wrvz-psew.json'
    return await fetch_data(session, url=url, params=params)

def produce_async(sublist):
    count = 0
    for item in sublist:
        try:
            item['extracted_ts'] = time.time()
            p.send_record(item)        
        except TypeError as typeerr:
            print(f'Non blocking error encountered producing record to kafka. Error: {typeerr}')
            print(f'record: {item}')
        except Exception as e:
            print(f'Blocking error encountered producing record to kafka. Error: {e}')
            print(f'record: {item}')
            raise e
        else: 
            count += 1
    return count

async def fetch_all_data(total):
    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        page_size = 10000
        page_num = 0
        count = 0 
        while count < total:
            print('gathering data for 5 pages...')
            page_data = await asyncio.gather(*(fetch_page(session, page_size, page_num + i) for i in range(5)))
            if not any(page_data):
                break
            page_num += 5
            for sublist in page_data:
                print('streaming data...')
                count += produce_async(sublist)
        return count

async def main():
    total = 100000 # replace with the total number of records you want to retrieve
    count = await fetch_all_data(total)
    print(f'Fetched {count} records')
    

if __name__ == '__main__':
    p = TaxiProducer()  
    start = datetime.now()
    print('async call initiated...')
    asyncio.run(main())
    print('async call finished and data streamed...', datetime.now()-start)






