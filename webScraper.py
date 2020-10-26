import requests
import sys
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
import logging
import argparse
import os

import chart_studio.plotly as py
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
#from plotly.offline import init_notebook_mode, iplot
#init_notebook_mode(connected=True)
pio.renderers.default = "browser"

# Logging setup
logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
log = logging.getLogger()
log.addHandler(handler)
log.setLevel(os.environ.get("LOGLEVEL", "INFO"))

ap = argparse.ArgumentParser()

ap.add_argument("-u", "--url", type=str, default='http://www.imdb.com/chart/top', help="url of target website")
ap.add_argument("-p", "--path", type=str, help="result local destination", required=True)
ap.add_argument("-g", "--graph", type=bool, default=True, help="data visualization")
args = vars(ap.parse_args())

# class declaration
class MovieScraper:

    # definition of arhuments for class initialization
    def __init__(self, url, path, visualize = True):

        self.url = url
        self.path = path
        self.visualize = visualize

    # function for information parsing of single "tr" item
    def item_parser(self, item):

        try:

            # Getting all important information with item parsing and some regular expression operations
            year = int(re.findall(r'\d+', item.find('td', {'class': 'titleColumn'}).find('span', {'class': 'secondaryInfo'}).contents[0])[0])
            title = item.find('td', {'class': 'titleColumn'}).find('a').contents[0]
            rating = float(item.find('td', {'class': 'ratingColumn imdbRating'}).find('strong').contents[0])
            people = re.findall(r'(?<=title=\").*(?=\">)', str(item.find('td', {'class': 'titleColumn'}).find('a')))[0].split(',')
            
            # cleaning whitespaces
            director = [" ".join(person.split('(')[0].split()) for i, person in enumerate(people) if i == 0][0]
            actors = [" ".join(person.split()) for i, person in enumerate(people) if i != 0]
                

            return {'title': title, 'year': year, 'rating': rating, 'director': director, 'actors': actors}

        except Exception as e: log.error('Error while item parsing: %s' % e)

    # function for some nice visualization of collected dataframe
    def visualizer(self, data):

        try:

            # copying data for modifications
            dataframe = data.copy()
            # Creating new variable of truncated title. If string is too long, it causes problems with visualization.
            dataframe['title_short'] = [title[:min(len(title), 50)] for title in list(dataframe['title'])]


            hover_text = []
            bubble_size = []

            # Formatting text description for data points
            for index, row in dataframe.iterrows():

                hover_text.append(('Title: {title}<br>'+
                                'Year: {year}<br>'+
                                'Director: {dir}<br>'+
                                'Rating: {rate}<br>'+
                                'Actors:{actors}<br>').format(title=row['title_short'],
                                                        year=row['year'],
                                                        dir=row['director'],
                                                        rate=row['rating'],
                                                        actors=row['actors']))

                # computation of graph point size based on 'rating' value
                bubble_size.append(10*(row['rating']-dataframe['rating'].min())+3) 

            # Addition of two variables into dataframe
            dataframe['text'] = hover_text
            dataframe['size'] = bubble_size

            # Parameter for graph point size tunning
            sizeref = 2.*max(dataframe['size'])/(20**2) 

            # Dictionary with dataframes for each director
            director_names = list(dataframe['director'].unique())
            director_data = {director:dataframe.query('director == "%s"' %director) for director in director_names}

            # Create figure
            fig = go.Figure()

            for director_name, director_movies in director_data.items():
                fig.add_trace(go.Scatter(
                    x=director_movies['year'], y=director_movies['rating'],
                    name=director_name, text=director_movies['text'],
                    marker_size=director_movies['size'],
                    ))

            # Tune marker appearance and layout
            fig.update_traces(mode='markers', marker=dict(sizemode='area', sizeref=sizeref, line_width=2))

            fig.update_layout(
                title='Release year and rating of movies',
                xaxis=dict(
                    title='year',
                    gridcolor='white',
                    type='log',
                    gridwidth=2,
                ),
                yaxis=dict(
                    title='rating',
                    gridcolor='white',
                    gridwidth=2,
                ),
                paper_bgcolor='rgb(243, 243, 243)',
                plot_bgcolor='rgb(243, 243, 243)',
                height = 700, width = 1500
            )

            # image export
            fig.write_image(self.path + 'scatter.png')
            fig.show()

        except Exception as e: log.error('Error while data visualization: %s' % e)


    # function, which executes data collection from website, creates structured data table and visualize graph (if user sets visualize parameter as True)
    def run_scraper(self):

        try:
            
            log.info('MovieScraper: Collecting data from: %s' % self.url)
            response = requests.get(self.url)
            context = BeautifulSoup(response.text, features="html.parser")

            items = context.findChildren("tr")

            data = []

            # Iteration through "tr" class items
            for i,movie in enumerate(items):
                
                # checking if item contains data
                if movie.find('td'):

                    # parsing item
                    info = self.item_parser(movie)

                    # collecting data in list
                    data.append(dict(zip(('title', 'year', 'rating', 'director', 'actors'),
                    (info['title'], info['year'], info['rating'], info['director'], info['actors']))))
            
            # Generation of pandas dataframe
            data = pd.DataFrame(data)

            # Export of data table as csv file
            data.to_csv(self.path+'result.csv')

            if self.visualize == True: self.visualizer(data)

        except Exception as e: log.error('Error while running web scraper: %s' % e)

if __name__ == '__main__':

    #initialize and run movie scraper
    MS = MovieScraper(args['url'], args['path'], args['graph'])
    MS.run_scraper()