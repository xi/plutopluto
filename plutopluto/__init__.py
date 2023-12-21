#!/usr/bin/env python

import argparse
import datetime
import os
import sys
from time import mktime
from time import time
from xml.sax.saxutils import escape

import aiohttp
import feedparser
from aiohttp import web
from feedparser.sanitizer import _sanitize_html
from flask import Flask
from flask import request
from flask import jsonify
from flask import abort

__version__ = '1.2.0'

app = Flask(__name__)


async def fetch(url, *, raw=False, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, **kwargs) as response:
            if response.status == 404:
                raise web.HTTPNotFound
            if response.status == 429:
                raise web.HTTPServiceUnavailable
            response.raise_for_status()
            if raw:
                return await response.read()
            else:
                return await response.json()


def linebreaks(text):
    html = (
        text
        .replace('\n\n', '</p><p>')
        .replace('\n', '<br>')
    )
    return '<p>' + html + '</p>'


async def parse_feed(url):
    """Get feed and convert to JSON."""

    feed = feedparser.parse(await fetch(url, raw=True))

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


async def parse_activity_stream(url):
    data = await fetch(url, headers={'Accept': 'application/activity+json'})
    entries = []

    def _parse_item(obj):
        source = obj.get('audience', obj['attributedTo'])

        content = _sanitize_html(obj.get('content', ''), 'utf-8', 'text/html')
        for attachment in obj.get('attachment', []):
            href = escape(attachment.get('href', attachment.get('url', '')))
            if href:
                ext = href.rsplit('.', 1)[-1]
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    content += f'<img src="{href}" alt="">'
                else:
                    content += f'<p><a href="{href}">{href}</a></p>'
            else:
                print(attachment)

        return {
            'id': obj['id'],
            'title': obj.get('name', ''),
            'link': obj.get('url', obj['id']),
            'source': source.split('/')[-1],
            'source_link': source,
            'content': content,
            'dt': datetime.datetime.fromisoformat(obj['published']).timestamp(),
            # attachments
        }

    def _process_activity(activity):
        if activity['type'] == 'Create':
            entries.append(_parse_item(activity['object']))
        elif activity['type'] == 'Announce':
            if isinstance(activity['object'], dict):
                _process_activity(activity['object'])

    for activity in data['orderedItems']:
        _process_activity(activity)

    return {
        'url': url,
        'next': data.get('next'),
        'entries': entries,
    }


@app.route('/parse', methods=['GET'])
async def _parse():
    if 'url' not in request.values:
        abort(400)

    url = request.values['url']

    try:
        if 'outbox' in url:
            data = await parse_activity_stream(url)
        else:
            data = await parse_feed(url)
    except Exception as err:
        app.logger.warning('%s: %s' % (url, err))
        abort(500)

    return jsonify(data)


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
    parser.add_argument('--port', type=int, default=8000)
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

    app.run('localhost', args.port)


if __name__ == '__main__':
    main()
