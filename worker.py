import tweepy
import requests
import threading
import os
from pymongo import MongoClient


client = MongoClient(os.environ['MONGO_URL'])
collection = client.projects.yomeerkat

#config

TWITTER_CONSUMER_TOKEN = os.environ['TWITTER_CONSUMER_TOKEN']
TWITTER_CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']
	
YO_API_TOKEN = os.environ['YO_API_TOKEN']

listeners = {}

def get_redirected_url(starturl):
	return requests.head(starturl, timeout=100.0 , headers={'Accept-Encoding': 'identity'}).headers.get('location', starturl)


class MyStreamListener(tweepy.StreamListener):

	yo_username = None
	twitter_username = None
	friends_ids = []

	def on_status(self, status):

		if str(status.user.id) in self.friends_ids and 'meerkat' in status.text and '|LIVE NOW|' in status.text and status.retweeted == False:
			try:
				print status
				url = status.entities['urls'][0]['expanded_url']
				meerkat_url = get_redirected_url(url)
				streaming_user = status.user.screen_name
				stream_id = meerkat_url.split('/')[-1]
				if len(stream_id) > 0:
					yo_meerkat_url = 'http://www.yomeerkat.co/mobile?stream_id=' + stream_id + '&streaming_user=' + streaming_user
					print 'sending a Yo to ' + self.yo_username
					res = requests.post('http://api.justyo.co/yo/', {'context': '@' + streaming_user,
																	 'username': self.yo_username,
																	 'link': yo_meerkat_url, 
																	 'api_token': YO_API_TOKEN})
					print res
				else:
					print 'No stream id found'
			except Exception as e:
				print e.message


def work():

	results = collection.find({})

	for entry in results:

		yo_username = entry.get('yo_username')
		twitter_username = entry.get('twitter_username')

		print 'running for ' + yo_username

		if listeners.get(yo_username) is None:

			print 'listening for ' + yo_username

			auth = tweepy.OAuthHandler(TWITTER_CONSUMER_TOKEN, TWITTER_CONSUMER_SECRET)
			auth.set_access_token(entry.get('access_token'), entry.get('access_token_secret'))

			api = tweepy.API(auth)

			friends_ids = []
			for friend_id in tweepy.Cursor(api.friends_ids).items():
			    friends_ids.append(str(friend_id))

			myStreamListener = MyStreamListener()
			myStreamListener.yo_username = yo_username
			myStreamListener.friends_ids = friends_ids
			myStreamListener.twitter_username = twitter_username
			myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
			myStream.filter(follow=friends_ids, async=True)

			listeners[yo_username] = myStreamListener

	threading.Timer(60, work).start()

	
if __name__ == "__main__":
	work()
