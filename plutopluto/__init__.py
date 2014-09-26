#!/usr/bin/env python

import sys
import os
from time import mktime, time
import argparse

from flask import Flask, request, jsonify, abort
from werkzeug.contrib.cache import SimpleCache

import feedparser
from bs4 import BeautifulSoup


app = Flask(__name__)
cache = SimpleCache()


def strip_atts(s):
	"""Strip possibly dangerous HTML attributes."""

	whitelist = ['href', 'src', 'alt', 'title', 'datetime']
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
	"""Get feed and convert to JSON."""

	feed = feedparser.parse(url)

	def _parse_item(item):
		d = dict()
		d['dt'] = (mktime(item['published_parsed']) if 'published_parsed' in item
			else int(time()))
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
		return d

	return {
		'url': url,
		'entries': map(_parse_item, feed.entries),
	}


def cachedParse(url, timeout=5 * 60):
	data = cache.get(url)
	if data is None:
		data = parse(url)
		cache.set(url, data, timeout=timeout)
	return data


@app.route('/parse', methods=['GET'])
def _parse():
	if 'url' in request.values:
		url = request.values['url']

		try:
			data = cachedParse(url)
		except Exception as err:
			app.logger.warning('%s: %s' % (url, err))
			data = {}

		return jsonify(data)
	else:
		abort(400)


@app.route('/', methods=['GET'])
def index():
	with open(os.path.join(app.root_path, 'index.html')) as fh:
		return fh.read()


@app.route('/config', methods=['GET'])
def config():
	return jsonify({
		'urls': app.config['URLS']
	})


def main():
	parser = argparse.ArgumentParser(description='simple feed aggregator')
	parser.add_argument('-d', '--debug', action='store_true')
	parser.add_argument('-c', '--config', metavar='FILE')
	parser.add_argument('urls', metavar='URL', nargs='*',
		help='full feed url, optionally with a {page} placeholder')
	args = parser.parse_args()

	if args.config:
		app.config.from_pyfile(os.path.abspath(args.config))
	app.debug = args.debug
	app.config['URLS'] = args.urls + app.config.get('URLS', [])

	if not app.config['URLS']:
		print("Error: No urls provided")
		parser.print_usage()
		sys.exit(1)

	app.run(app.config.get('HOST'), app.config.get('PORT'))


if __name__ == '__main__':
	main()
