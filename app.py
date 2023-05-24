from flask import Flask, request, render_template
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, IntegerField, validators
import requests
import os
import json

# create an instance of a Flask web app and call it app
app = Flask(__name__)
app.config['SECRET_KEY']=os.urandom(16).hex()


""" ----------- I - JSON DOCUMENTS ----------- """
def save_to_file(data,filename):
    with open(filename,'w') as write_file:
        json.dump(data,write_file,indent=2)

def read_from_file(filename):
    with open(filename,'r') as read_file:
        data = json.load(read_file)
    return data

""" ----------- 2 - API KEY ----------- """
# read from the api_key.json file and assign your API key to a variable named api_key
with open('api_key.json', 'r') as f:
    data = json.load(f)

api_key = data['key']

""" ----------- 3 - USEFUL LISTS ----------- """
# read from the countries.json file and assign its value to a variable named countries
with open('countries.json', 'r') as f:
    countries = json.load(f)
countries_list = list(countries.keys()) #this line of code is done for you, it creates a list containing all the country names

# variable charts is done for you, it provides a list of possible chart names for the user to select from
charts = [("top", "Editorial Chart"),
          ("hot", "Most viewed lyrics in the last 2 hours"),
          ("mxmweekly", "Most viewed lyrics in the last 7 days"),
          ("mxmweekly_new", "Most viewed lyrics in the last 7 days limited to new releases only")]

# variable number of results is done for you, it provides 4 options for the user to select from
number_of_results = [5,10,15,20]

""" ----------- FORMS ----------- """
# define a class named Search and include 3 input fields:
# - select field named country
# - select field named chartType
# - integer field named numberResults (let the user only enter an integer from 1 to 10)

class Search(FlaskForm):
    country = SelectField('Country', choices=countries_list)
    chart_type = SelectField('Chart Type', choices=charts)
    number_results = IntegerField('Number of Results', [validators.NumberRange(min=1, max=10)])
    submit = SubmitField('Search')
    
""" ----------- API CALLS ----------- """
# complete this function definition by filling out the missing:
#  - input arguments of the function
#  - the API request to the defined url
#  - saving the response of the API request to file
#  - returning the response of the API request

def request_top_artists(country_code, number_of_results, api_key):
    top_artists_url="https://api.musixmatch.com/ws/1.1/chart.artists.get?country={0}&page_size={1}&apikey={2}"\
        .format(country_code, number_of_results, api_key)
    response = requests.get(top_artists_url)
    
    with open('top_artists.json', 'w') as f:
        f.write(response.text)
    
    return response.json()

# complete this function definition by filling out the missing:
#  - input arguments of the function
#  - the API request to the defined url
#  - saving the response of the API request to file
#  - returning the response of the API request

def request_top_tracks(country_code, chart_name, number_of_results, api_key):
    top_tracks_url = f"https://api.musixmatch.com/ws/1.1/chart.tracks.get?country={country_code}&chart_name={chart_name}&page_size={number_of_results}&apikey={api_key}&has_lyrics=true"
    response = requests.get(top_tracks_url)

    with open('top_tracks.json', 'w') as f:
        f.write(response.text)

    return response.json()

@app.route('/', methods=["GET","POST"])
def index():
    form = Search()

    if request.method == "POST":

        country = request.form["country"]
        chart_type = request.form["chartType"]
        number_results = request.form["numberResults" ]      
        artists = request_top_artists(country, number_results, api_key)
        tracks = request_top_tracks(country, chart_type, number_results, api_key)
        
        return render_template("results.html", country=country, chart_type=chart_type, quantity=number_results, artists=artists, tracks=tracks)
    return render_template("index.html", form=form, list_of_artists=[], list_of_tracks=[], country_options=countries_list)



@app.route('/results', methods=["POST"])
def results():
    form = Search()
    if request.method == "POST":
        quantity = request.form.get("numberResults")
        country = request.form.get("country")
        chart_type = request.form.get("chartType")
        artists = request_top_artists(country, quantity, api_key)
        tracks = request_top_tracks(country, chart_type, quantity, api_key)

        list_of_artists = []
        for artist in artists['message']['body']['artist_list']:
            list_of_artists.append(artist['artist']['artist_name'])

        list_of_tracks = []
        for track in tracks['message']['body']['track_list']:
            track_name = track['track']['track_name']
            artist_name = track['track']['artist_name']
            share_url = track['track']['track_share_url']
            list_of_tracks.append({'track_name': track_name, 'artist_name': artist_name, 'track_share_url': share_url})

        return render_template('results.html', list_of_artists=list_of_artists, list_of_tracks=list_of_tracks, country=country, quantity=quantity)

    return render_template("index.html", form=form, list_of_artists=[], list_of_tracks=[], country_options=countries_list)


@app.route('/lyrics/<int:track_id>')
def lyrics(track_id):

    
    url = f'https://api.musixmatch.com/ws/1.1/track.lyrics.get?track_id={track_id}&apikey=39028468e0880621b9c45c326ccf4ec8'
    response = requests.get(url)
    data = response.json()

    if 'message' in data and 'body' in data['message'] and 'lyrics' in data['message']['body']:
        lyrics_body = data['message']['body']['lyrics']['lyrics_body']
        print(lyrics_body)
        return render_template('lyrics.html', lyrics=lyrics_body)
    
    else:
        print(data)
        return render_template('lyrics.html', lyrics=None)

if __name__ == '__main__':
    app.run(port=5000,debug=True)