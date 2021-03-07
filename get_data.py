import wikipedia
from rotten_tomatoes_scraper.rt_scraper import MovieScraper
from imdb import IMDb
import pandas as pd
import numpy as np
from requests import get
from bs4 import BeautifulSoup
from time import sleep
from random import randint
import re


def get_RT_ratings(movie_title):
    """
    Returns the Rotten Tomatoes critic score and audience score of a title
    """
    movie_scraper = MovieScraper(movie_title=movie_title)
    movie_scraper.extract_metadata()
    rt_critics_score = int(movie_scraper.metadata['Score_Rotten'])
    rt_audience_score = int(movie_scraper.metadata['Score_Audience'])
    return rt_critics_score, rt_audience_score


def get_IMDB_ratings(movie_title):
    """
    Returns the IMDB rating of a title
    """
    ia = IMDb()
    res = ia._search_movie('the matrix (1999)', results=True)
    movie_ID = res[0][0]
    if res[0][1]['title'] != movie_title:
        print('Titles do not exactly match: ', movie_title, res[0][1]['title'])
    movie = ia.get_movie(movie_ID)
    rating = movie.data['rating']
    return rating


def get_metacritic_scores(movie_title):
    """
    Returns Metacritic score and Metacritic user score of a title
    by scraping the Metacritic website
    """
    movie_title = movie_title.replace(' ', '-')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
    movie = get('https://www.metacritic.com/movie/' + movie_title, headers=headers)
    movie_soup = BeautifulSoup(movie.text, 'html.parser')
    metascore_elem = movie_soup.find_all("div", class_="metascore_w larger movie positive")[0]
    user_score_elem = movie_soup.find_all("div", class_="metascore_w user larger movie positive")[0]
    metascore = int(re.findall(r'\d{2}', str(metascore_elem))[0])
    user_score = float(re.findall(r'\d.\d', str(user_score_elem))[0])
    return metascore, user_score

""" BUILD DATABASE """

# TODO
#    download my watchlist from IMDB
#    add loop for movies
#    add sleep(randint(8,20)) for loop in metacritic
#    organize data into dataframe
