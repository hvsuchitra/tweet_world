import os
import base64
from concurrent.futures import ThreadPoolExecutor
from itertools import islice

import requests
import requests_cache

requests_cache.install_cache(cache_name='cache', backend='sqlite',
                             expire_after=86400)  # setup the cache for one day 86400 seconds = 24 hours

HASHTAG_COUNT = 25

# Twitter API Details
API_KEY_TWITTER = os.getenv('TWITTER_API_KEY')
API_SECRET_TWITTER = os.getenv('TWITTER_API_SECRET')
API_KEY_SECRET_TWITTER = base64.b64encode(f'{API_KEY_TWITTER}:{API_SECRET_TWITTER}'.encode('ascii')).decode('ascii')

# NEWS API Details
API_KEY_NEWS = os.getenv('NEWS_API')

# Twitter OAUTH Setup
auth_url = 'https://api.twitter.com/oauth2/token'
auth_headers = {'Authorization': f'Basic :{API_KEY_SECRET_TWITTER}',
                'Content-Type': 'application/x-www-form-urlencoded'}
auth_data = {'grant_type': 'client_credentials'}

response = requests.post(auth_url, headers=auth_headers, data=auth_data)
token = response.json()['access_token']  # Save the OAUTH Token that is needed in further API calls to twitter


def __get_news(tag):
    """Helper function that is run using threads
    Fetches news articles for the corresponding tag
    
    Args:
        tag (str): Hashtag to fetch news articles for
    
    Returns:
        tuple: Tuple of hashtag and list of news articles
    """
    url = 'https://newsapi.org/v2/everything?q={}&sortBy=popularity&apiKey={}&language=en'
    query_url = url.format(tag, API_KEY_NEWS)
    response = requests.get(query_url)
    contents = response.json()
    return tag, contents


def get_tags():
    """Generator that does a GET request to Twitter's "Trending Tags" Endpoint
    and yields trending hashtags
    
    Yields:
        str: Trending Hashtags
    """
    url = 'https://api.twitter.com/1.1/trends/place.json'
    all_data = requests.get(url, headers={'Authorization': f'Bearer {token}'}, params={'id': '2514815'}).json()[0]
    for i in all_data['trends']:
        yield i['name'].lstrip('#')


def get_news():
    """Calls NEWS API for a list of hashtags
    
    Returns:
        dict: Dictionary with keys as "hashtags" and values as "NEWS API result list"
    """
    needed_tags = islice(get_tags(), HASHTAG_COUNT)

    with ThreadPoolExecutor(max_workers=10) as executor:
        res = executor.map(__get_news, needed_tags)

    return dict(res)
