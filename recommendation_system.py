# -*- coding: utf-8 -*-
"""Recommendation System.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1q8uEKF6eHF6P-hdFTi4eO0rVYgwUNIrs

# Libraries
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

"""# Data Collection

Load the dataset
"""

movie_rating_df = pd.read_csv('https://dqlab-dataset.s3-ap-southeast-1.amazonaws.com/movie_rating_df.csv')

movie_rating_df.head()

movie_rating_df.info()

"""Other data: actors"""

actor_df = pd.read_csv('https://dqlab-dataset.s3-ap-southeast-1.amazonaws.com/actor_name.csv')

actor_df.head()

actor_df.info()

"""Other data: directors and writers"""

director_writer_df = pd.read_csv('https://dqlab-dataset.s3-ap-southeast-1.amazonaws.com/directors_writers.csv')

director_writer_df.head()

director_writer_df.info()

"""# Data Preparation

Convert directors and writers name into list data type because some movies have more than one director or writer
"""

director_writer_df['director_name'] = director_writer_df['director_name'].apply(lambda row: row.split(','))
director_writer_df['writer_name'] = director_writer_df['writer_name'].apply(lambda row: row.split(','))

director_writer_df.head()

"""In the actors dataframe, we only need to use column nconst, primaryName, and knownForTitles"""

actor_df = actor_df[['nconst','primaryName','knownForTitles']]
actor_df.head()

"""Check variations"""

actor_df['knownForTitles'].apply(lambda x: len(x.split(','))).unique()

"""An actor may star in some movies, so we'll convert knownForTitles column into a list data type."""

actor_df['knownForTitles'] = actor_df['knownForTitles'].apply(lambda x: x.split(','))
actor_df.head()

"""Correspondence 1-1"""

df_uni = []

for x in ['knownForTitles']:
  idx = actor_df.index.repeat(actor_df['knownForTitles'].str.len())
  df1 = pd.DataFrame({
      x: np.concatenate(actor_df[x].values)
  })
  df1.index = idx
  df_uni.append(df1)

df_concat = pd.concat(df_uni, axis=1)
unnested_df = df_concat.join(actor_df.drop(['knownForTitles'], 1), how='left')
unnested_df = unnested_df[actor_df.columns.tolist()]
unnested_df.head()

"""Group primaryName into a list group by knownForTitles"""

unnested_drop = unnested_df.drop(['nconst'], axis=1)

df_uni = []

for col in ['primaryName']:
  dfi = unnested_drop.groupby(['knownForTitles'])[col].apply(list)
  df_uni.append(dfi)
df_grouped = pd.concat(df_uni, axis=1).reset_index()
df_grouped.columns = ['knownForTitles','cast_name']
df_grouped.head()

"""Join movie_rating_df, actor_df, and director_writer_df """

base_df = pd.merge(df_grouped, movie_rating_df, left_on='knownForTitles', right_on='tconst', how='inner')
base_df = pd.merge(base_df, director_writer_df, left_on='tconst', right_on='tconst', how='left')
base_df.head()

"""# Data Cleaning"""

base_drop = base_df.drop(['knownForTitles'], axis=1)
base_drop.info()

base_drop['genres'] = base_drop['genres'].fillna('Unknown')

base_drop.isnull().sum()

base_drop[['director_name','writer_name']] = base_drop[['director_name','writer_name']].fillna('Unknown')

"""We always convert a column consisting of multiple values ​​into a list data type"""

base_drop['genres'] = base_drop['genres'].apply(lambda x: x.split(','))

"""Reformat base_df"""

base_drop2 = base_drop.drop(['tconst','isAdult','endYear','originalTitle'], axis=1)
base_drop2 = base_drop2[['primaryTitle','titleType','startYear','runtimeMinutes','genres','averageRating','numVotes','cast_name','director_name','writer_name']]
base_drop2.columns = ['title','type','start','duration','genres','rating','votes','cast_name','director_name','writer_name']
base_drop2.head()

"""Metadata classification"""

feature_df = base_drop2[['title','cast_name','genres','director_name','writer_name']]
feature_df.head()

"""# Recommender System

Create a function to strip spaces of each row and each of its elements
"""

def sanitize(x):
  try:
    if isinstance(x, list):
      return [i.replace(' ','').lower() for i in x]
    else:
      return [x.replace(' ','').lower()]
  except:
    print(x)

feature_cols = ['cast_name','genres','writer_name','director_name']

for col in feature_cols:
  feature_df[col] = feature_df[col].apply(sanitize)

"""Create a function to make metadata soup (combine all features into 1 sentence) for each title"""

def soup_feature(x):
  return ' '.join(x['cast_name']) + ' ' + ' '.join(x['genres']) + ' ' + ' '.join(x['director_name']) + ' ' + ' '.join(x['writer_name'])

feature_df['soup'] = feature_df.apply(soup_feature, axis=1)

"""Prepare a CountVectorizer (stop_words = english) and fit with the soup we made above"""

count = CountVectorizer(stop_words='english')
count_matrix = count.fit_transform(feature_df['soup'])
print(count)
count_matrix.shape

"""Create a similarity model between matrices"""

cosine_sim = cosine_similarity(count_matrix, count_matrix)
cosine_sim

"""Content Based Recommender System"""

indices = pd.Series(feature_df.index, index=feature_df['title']).drop_duplicates()

def content_recommender(title):
  idx = indices[title]
  sim_scores = list(enumerate(cosine_sim[idx]))
  sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
  sim_scores = sim_scores[1:11]
  movie_indices = [i[0] for i in sim_scores]
  return base_df.iloc[movie_indices]

content_recommender('The Lion King')