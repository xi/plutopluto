#!/usr/bin/env python

from time import mktime, time
import argparse

from flask import Flask, request, jsonify, abort, render_template

import feedparser
from bs4 import BeautifulSoup


app = Flask(__name__)


def strip_atts(s):
	whitelist = ['href', 'src', 'alt', 'title']
	tree = BeautifulSoup(s)

	for tag in tree.find_all():
		l = []
		for attr in tag.attrs:
			if attr not in whitelist:
				l.append(attr)
		for attr in l:
			del tag.attrs[attr]
	return unicode(tree)


def parse(url):
	feed = feedparser.parse(url)

	entries = []

	for item in feed.entries:
		d = dict()
		d['dt'] = mktime(item['published_parsed']) if 'published_parsed'in item else int(time())
		d['id'] = item['id']
		d['title'] = item['title']
		d['link'] = item['link']
		d['source'] = feed.feed['title']
		if 'gdata.youtube' in url:
			tree = BeautifulSoup(item['description'])
			head = tree.find_all('a')[1]
			img = tree.find_all('a')[0]
			d['content'] = strip_atts(unicode(head) + ' ' + unicode(img))
		else:
			d['content'] = strip_atts(item['description'])
		entries.append(d)

	return {
		'url': url,
		'entries': entries,
	}


@app.route('/parse', methods=['GET'])
def main():
	if 'url' in request.values:
		url = request.values['url']

		try:
			data = parse(url)
		except Exception as err:
			print(err)
			data = {}

		return jsonify(data)
	else:
		abort(400)


@app.route('/', methods=['GET'])
def index():
	with open('index.html') as fh:
		html = fh.read()

	return html


@app.route('/config', methods=['GET'])
def  config():
	return jsonify({
		'urls': app.config['URLS']
	})


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--debug', action='store_true')
	parser.add_argument('urls', metavar='url', nargs='+')
	args = parser.parse_args()

	app.debug = args.debug
	app.config['URLS'] = args.urls
	app.run()
