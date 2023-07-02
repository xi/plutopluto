#!/usr/bin/env python

import argparse
import functools
import os
import sys
from time import mktime
from time import time

import feedparser
from bs4 import BeautifulSoup
from flask import Flask
from flask import request
from flask import jsonify
from flask import abort

__version__ = '1.2.0'

app = Flask(__name__)


def linebreaks(text):
    html = (
        text
        .replace('\n\n', '</p><p>')
        .replace('\n', '<br>')
    )
    return '<p>' + html + '</p>'


@functools.lru_cache
def parse(url):
    """Get feed and convert to JSON."""

    feed = feedparser.parse(url)

    def _parse_item(i, item):
        d = dict()
        if 'published_parsed' in item:
            d['dt'] = mktime(item['published_parsed'])
        elif 'updated_parsed' in item:
            d['dt'] = mktime(item['updated_parsed'])
        else:
            d['dt'] = int(time()) - i  # - i to preserve sort order
        d['id'] = item.get('id')
        d['title'] = item.get('title')
        d['link'] = item.get('link')
        d['source'] = feed.feed.get('title')
        d['source_link'] = feed.feed.get('link')
        d['content'] = item.get('description', '')
        if '<' not in d['content']:
            d['content'] = linebreaks(d['content'])
        if 'youtube' in url:
            thumbnail = '<a href="%s"><img alt="" src="%s" /></a>' % (
                d['link'],
                item['media_thumbnail'][0]['url'],
            )
            d['content'] = thumbnail + d['content']
        return d

    return {
        'url': url,
        'entries': [_parse_item(i, item) for i, item in enumerate(feed.entries)],
    }


@app.route('/parse', methods=['GET'])
def _parse():
    if 'url' in request.values:
        url = request.values['url']

        try:
            data = parse(url)
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
    parser.add_argument('--version', '-V', action='version', version=__version__)
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
