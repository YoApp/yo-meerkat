import os
import flask 
import tweepy
from pymongo import MongoClient
from flask import Flask
from flask import request, render_template


app = Flask(__name__)

client = MongoClient(os.environ['MONGO_URL'])
collection = client.projects.yomeerkat

# Twitter API
TWITTER_CONSUMER_TOKEN = os.environ['TWITTER_CONSUMER_TOKEN']
TWITTER_CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']
TWITTER_CALLBACK_URL = os.environ['TWITTER_CALLBACK_URL']


session = {}


@app.route("/")
def index():
	return render_template('index.html')


@app.route("/success")
def success():
	return render_template('success.html')


@app.route("/mobile")
def mobile():
	streaming_user = request.args.get('streaming_user')
	stream_id = request.args.get('stream_id')
	browser_url = 'http://meerkatapp.co/' + streaming_user.lower() + '/' + stream_id
	native_app_url = 'meerkat://live/' + stream_id
	return render_template('mobile.html', native_app_url=native_app_url, browser_url=browser_url)


@app.route("/authorize")
def authorize():
	auth = tweepy.OAuthHandler(TWITTER_CONSUMER_TOKEN, 
		TWITTER_CONSUMER_SECRET, TWITTER_CALLBACK_URL)
	
	try: 
		#get the request tokens
		redirect_url= auth.get_authorization_url()
		session['request_token'] = auth.request_token
		session['yo_username'] = request.args.get('yo_username')
	except tweepy.TweepError:
		print 'Error! Failed to get request token'
	
	return flask.redirect(redirect_url)	


@app.route("/verify")
def get_verification():

	#get the verifier key from the request url
	verifier= request.args['oauth_verifier']
	auth = tweepy.OAuthHandler(TWITTER_CONSUMER_TOKEN, TWITTER_CONSUMER_SECRET)
	token = session.get('request_token')
	del session['request_token']
	auth.request_token = token
	try:
	    auth.get_access_token(verifier)
	except tweepy.TweepError:
		print 'Error! Failed to get access token.'

	api = tweepy.API(auth)
	twitter_username = api.me().screen_name
	
	#store in a db
	key = {'access_token': auth.access_token}
	data = {'access_token': auth.access_token, 'access_token_secret': auth.access_token_secret, 'yo_username': session['yo_username'], 'twitter_username': twitter_username}
	collection.update(key, data, upsert=True);

	return render_template('success.html')
	

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
