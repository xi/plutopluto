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

	def _parse_item(args):
		i, item = args
		d = dict()
		if 'published_parsed' in item:
			d['dt'] = mktime(item['published_parsed'])
		else:
			d['dt'] = int(time()) - i  # - i to preserve sort order
		d['id'] = item.get('id')
		d['title'] = item.get('title')
		d['link'] = item.get('link')
		d['source'] = feed.feed.get('title')
		if 'youtube' in url:
			template = u'<img alt="%s" src="%s" />\n<div>%s</div>'
			d['content'] = strip_atts(template % (
				item['media_content'][0]['url'],
				item['media_thumbnail'][0]['url'],
				item['media_description']))
		elif 'content' in item:
			d['content'] = strip_atts(item['content'][0]['value'])
		else:
			d['content'] = strip_atts(item.get('description'))
		return d

	return {
		'url': url,
		'entries': map(_parse_item, enumerate(feed.entries)),
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
			abort(500)

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

	config_name = '.plutopluto.cfg'
	local_config = os.path.abspath(config_name)
	home_config = os.path.expanduser('~/' + config_name)

	if args.config:
		app.config.from_pyfile(os.path.abspath(args.config))
	elif os.path.exists(local_config):
		app.config.from_pyfile(local_config)
	elif os.path.exists(home_config):
		app.config.from_pyfile(home_config)
	app.debug = args.debug
	app.config['URLS'] = args.urls + app.config.get('URLS', [])

	if not app.config['URLS']:
		print("Error: No urls provided")
		parser.print_usage()
		sys.exit(1)

	app.run(app.config.get('HOST'), app.config.get('PORT'))


if __name__ == '__main__':
	main()
