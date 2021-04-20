# Imports
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
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn import tree
from sklearn.externals.six import StringIO
import matplotlib.pyplot as plt
import pydot

# Settings
pd.options.mode.chained_assignment = None


def get_RT_ratings_og(movie_title):
    """
    Returns the Rotten Tomatoes critic score and audience score of a title
    """
    movie_scraper = MovieScraper(movie_title=movie_title)
    movie_scraper.extract_metadata()
    rt_critics_score = int(movie_scraper.metadata['Score_Rotten'])
    rt_audience_score = int(movie_scraper.metadata['Score_Audience'])
    return rt_critics_score, rt_audience_score


def get_RT_ratings(movie_title, year):
    """
    Returns the Rotten Tomatoes critic score and audience score of a title
    """

    # Extract URL
    RT_search = MovieScraper()

    search_res = RT_search.search(movie_title)

    # Exact match
    url_list = [movie_dict['url'] for movie_dict in search_res['movies']
                if movie_dict['name'].lower() == movie_title.lower()]
    if len(url_list) == 1:
        url = url_list[0]
    # No exact match -  return the latest one
    elif not url_list:
        url_list = sorted([(movie_dict['url'], movie_dict['year']) for movie_dict in search_res['movies']],
                          key=lambda x: x[1], reverse=True)
        url = url_list[0][0]
        print(f'No exact match found. Going with {url}')
    # More than one exact match - return the one with the shortest title
    elif len(url_list) > 1:
        url_list = sorted([(movie_dict['url'], movie_dict['year']) for movie_dict in search_res['movies']
                           if movie_dict['name'].lower() == movie_title.lower()],
                          key=lambda x: abs(x[1] - year), reverse=False)
        url = url_list[0][0]
        print(f'More than one exact match found. Going with {url}')

    movie_scraper = MovieScraper(movie_url='https://www.rottentomatoes.com' + url)
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
    movie_title = movie_title.replace(': ', '-').replace(' ', '-').lower()
    movie_title = movie_title.replace("'", '').replace(',', '').replace('.', '').replace('/', '')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
    movie = get('https://www.metacritic.com/movie/' + movie_title, headers=headers)
    movie_soup = BeautifulSoup(movie.text, 'html.parser')
    metascore_elems = []
    user_score_elems = []
    # Get metascores
    for r in ['positive', 'negative', 'mixed']:
        try:
            metascore_elems.append(movie_soup.find_all("div", class_=f"metascore_w larger movie {r}")[0])
        except:
            continue
    metascore = int(re.findall(r'\d{2}', str(metascore_elems[0]))[0])

    # Get user scores
    for r in ['positive', 'negative', 'mixed']:
        try:
            user_score_elems.append(movie_soup.find_all("div", class_=f"metascore_w user larger movie {r}")[0])
        except:
            continue
    user_score = float(re.findall(r'\d.\d', str(user_score_elems[0]))[0])

    return metascore, user_score


""" BUILD DATABASE """


def build_database(filename='ratings.csv'):
    # Load my IMDB ratings
    df = pd.read_csv(filename, encoding='latin1')

    # Keep only movies
    df = df[df['Title Type'] == 'movie']
    df = df[['Title', 'IMDb Rating', 'Your Rating', 'Year']]

    # Delete some titles where RT ratings don't exist or can't be found with the API
    # (due to being too niche or their title is too common)
    df = df[~df['Title'].isin(['Berlin Calling', 'Boy', 'The King', 'Boy', 'Wonder',
                               'The Chronicles of Narnia: The Lion, the Witch and the Wardrobe',
                               'VAN valami furcsa és megmagyarázhatatlan', 'Teströl és lélekröl',
                               'Aurora Borealis: Északi fény', 'Ruben Brandt, a gyujto', 'Loro 1', 'A Viszkis',
                               'Kojot'])]

    # Initialize values
    df['Metascore'] = np.nan
    df['RT Audience'] = np.nan
    df['RT Critics'] = np.nan
    problematic_rt = []
    problematic_meta = []

    for title, year in df.loc[df['Metascore'], ['Title', 'Year']].values:

        # Hardcoding some fixes:
        manual_titlefix_RT = {"Bienvenue chez les Ch'tis": "Welcome to the sticks",
                              'Léon': "Léon: The Professional",
                              'La vita è bella': 'La vita è bella (Life Is Beautiful)',
                              'Iron Man Three': 'Iron Man 3',
                              'Borat Subsequent Moviefilm: Delivery of Prodigious Bribe to American Regime for Make Benefit Once Glorious Nation of Kazakhstan': 'Borat: Subsequent Moviefilm',
                              'The Butler': "Lee Daniels' The Butler",
                              'Edge of Tomorrow': 'Live Die Repeat: Edge of Tomorrow',
                              'Mulholland Dr.': 'Mulholland Drive',
                              'Et soudain, tout le monde me manque': 'The Day I Saw Your Heart',
                              "Le fabuleux destin d'Amélie Poulain": 'Amelie From Montmartre',
                              'Turist': 'Force Majeure',
                              "La vie d'Adèle": 'Blue Is the Warmest Color',
                              'Sen to Chihiro no kamikakushi': 'Spirited Away',
                              'Star Wars: Episode VIII - The Last Jedi': 'Star Wars: The Last Jedi',
                              'Star Wars: Episode IX - The Rise of Skywalker': 'Star Wars: The Rise of Skywalker',
                              'Birdman or (The Unexpected Virtue of Ignorance)': 'Birdman',
                              'Kill Bill: Vol. 1': 'Kill Bill: Volume 1',
                              'Kill Bill: Vol. 2': 'Kill Bill: Volume 2',
                              "Qu'est-ce qu'on a fait au Bon Dieu?": 'Serial (Bad) Weddings',
                              'Fast & Furious 7': 'Furious 7',
                              'Hable con ella': 'Talk to Her',
                              'Mou gaan dou': 'Internal Affairs',
                              'De grønne slagtere': 'The Green Butchers',
                              "Jeux d'enfants": 'Love me if you dare',
                              'Oldeuboi': 'Oldboy',
                              'Kiss Kiss Bang Bang': 'Kiss Kiss, Bang Bang',
                              'Saul fia': 'Son of Saul',
                              'Mænd & høns': 'Men and Chicken',
                              'Das Leben der Anderen': 'The Lives of Others',
                              'El método': 'The Gronholm Method',
                              'Contratiempo': 'The Invisible Guest',
                              'The Godfather: Part II': 'The Godfather, Part II',
                              'Life of Brian': "Monty Python's Life of Brian",
                              'The Meaning of Life': "Monty Python's The Meaning of Life",
                              'When Harry Met Sally...': 'When Harry Met Sally'}
        manual_titlefix_meta = {'Léon': 'The Professional',
                                '(500) Days of Summer': '500 Days of Summer',
                                'La vita è bella': 'La vita è bella (Life Is Beautiful)',
                                'Borat Subsequent Moviefilm: Delivery of Prodigious Bribe to American Regime for Make Benefit Once Glorious Nation of Kazakhstan': 'Borat: Subsequent Moviefilm',
                                'The Butler': "Lee Daniels' The Butler",
                                'Et soudain, tout le monde me manque': 'The Day I Saw Your Heart',
                                "Le fabuleux destin d'Amélie Poulain": 'Amelie From Montmartre',
                                'Turist': 'Force Majeure',
                                "La vie d'Adèle": 'Blue Is the Warmest Color',
                                'Sen to Chihiro no kamikakushi': 'Spirited Away',
                                "Qu'est-ce qu'on a fait au Bon Dieu?": 'Serial (Bad) Weddings',
                                'Fast & Furious 7': 'Furious 7',
                                'Hable con ella': 'Talk to Her',
                                'Iron Man Three': 'Iron Man 3',
                                'Mou gaan dou': 'Internal Affairs',
                                'De grønne slagtere': 'The Green Butchers',
                                "Jeux d'enfants": 'Love me if you dare',
                                'Oldeuboi': 'Oldboy',
                                'Kiss Kiss Bang Bang': 'Kiss Kiss, Bang Bang',
                                'Saul fia': 'Son of Saul',
                                'Mænd & høns': 'Men and Chicken',
                                'Das Leben der Anderen': 'The Lives of Others',
                                'El método': 'The Gronholm Method',
                                'Contratiempo': 'The Invisible Guest',
                                'Life of Brian': "Monty Python's Life of Brian",
                                'The Meaning of Life': "Monty Python's The Meaning of Life",
                                'When Harry Met Sally...': 'When Harry Met Sally',
                                'Of Mice and Men': 'Of Mice and Men 1992',
                                'Druk': 'Another Round'}

        if title in ['Split', 'Samba']:  # year is incorrect
            year + 1
        if title in manual_titlefix_RT:  # title is different on Rotten Tomatoes
            title_rt = manual_titlefix_RT[title]
        else:
            title_rt = title
        if title in manual_titlefix_meta:  # title is different on Metacritic
            title_meta = manual_titlefix_meta[title]
        else:
            title_meta = title

        # Get Metascores
        try:
            meta_scores = get_metacritic_scores(title_meta)
            df.loc[df['Title'] == title, 'Metascore'] = meta_scores[0]
        except:
            problematic_meta.append(title_meta)
            print('Problematic:', title)

        # Get RT scores
        try:
            RT_scores = get_RT_ratings(title_rt, year)
            df.loc[df['Title'] == title, 'RT Critics'] = RT_scores[0]
            df.loc[df['Title'] == title, 'RT Audience'] = RT_scores[1]
        except:
            problematic_rt.append(title_meta)
            print('Problematic:', title)

    print('Database is (partially) ready. Fill the missing values for problematic titles')
    df.to_csv('data.csv', index=False)
    problematic_meta.to_csv('problematic_titles_meta.csv', index=False)
    problematic_rt.to_csv('problematic_titles_rt.csv', index=False)


def normalize(data):
    '''
    Bring all columns to the same 1-10 scale
    '''

    data['RT Critics'] /= 10
    data['RT Audience'] /= 10
    data['Metascore'] /= 10

    return data


def regression_model(data):
    """
    Model to answer the question - what rating would I give this movie?
    """
    # Extract X and y matrices
    X = data[['IMDb Rating', 'Metascore', 'RT Critics', 'RT Audience']]
    y = data['Your Rating']

    LR = LinearRegression(fit_intercept=False)
    LR.fit(X, y)
    coefs = LR.coef_

    return coefs


def classification_model(data):
    """
    Model to answer the question - would I like this movie?
    """
    # Extract X and y matrices
    X = data[['IMDb Rating', 'Metascore', 'RT Audience', 'RT Critics']]
    y = pd.Series(np.where((data['Your Rating'] >= 7), 'Like', 'Dislike')).astype('category')

    DT = DecisionTreeClassifier(max_depth=3, min_samples_leaf=0.02, min_impurity_decrease=0.005, ccp_alpha=0.003)
    DT.fit(X, y)

    fig = plt.figure(figsize=(25, 20))
    _ = tree.plot_tree(DT,
                       feature_names=['IMDb Rating', 'Metascore', 'RT Audience', 'RT Critics'],
                       class_names=['Disike', 'Like'], proportion=True, rounded=True, filled=True)
    fig.savefig('my_decision_tree.png')
    plt.close('all')


def predict_my_rating(coefs, imdb, metascore, rt_critics, rt_audience):
    metascore /= 100
    rt_critics /= 100
    rt_audience /= 100

    pred = np.dot(coefs, (imdb, metascore, rt_critics, rt_audience))
    return round(pred,2)


def run():
    # STEP 0: obtain database with helper functions

    # STEP 1: Preparations
    # Read data and drop NAs
    data = pd.read_csv('data.csv')
    data = data.dropna()

    # Get all variables to the same scale
    data = normalize(data)

    # STEP 2: Run models
    coefs = regression_model(data)
    #  Get decision tree
    classification_model(data)

    # Example prediction for Wonder Woman 1984
    print(predict_my_rating(coefs, imdb=5.4, metascore=60, rt_critics=59, rt_audience=74))
