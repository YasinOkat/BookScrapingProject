import plotly.graph_objects as go
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
database = client['smartmaple']
collection = database['kitapyurdu']

data = collection.find()

titles = []
ratings = []

for document in data:
    titles.append(document['title'])
    ratings.append(document['bought'])

client.close()

fig = go.Figure(data=go.Bar(x=titles, y=ratings))
fig.update_layout(
    title='Pages of Python Books',
    xaxis_title='Title',
    yaxis_title='Times bought'
)
fig.show()
