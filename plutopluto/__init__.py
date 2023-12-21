#!/usr/bin/env python

import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from time import mktime
from time import time
from xml.sax.saxutils import escape

import aiohttp
import feedparser
from aiohttp import web
from feedparser.sanitizer import _sanitize_html

__version__ = '1.2.0'

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
URLS = []


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
        escape(text)
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
            thumbnail = '<a href="{}" tabindex="-1"><img alt="" src="{}" /></a>'.format(
                escape(d['link']),
                escape(item['media_thumbnail'][0]['url']),
            )
            d['content'] = thumbnail + d['content']
        elif 'reddit' in url:
            d['content'] = (
                d['content']
                .replace('<table>', '')
                .replace('</table>', '')
                .replace('<tr>', '')
                .replace('</tr>', '')
                .replace('<td>', '')
                .replace('</td>', '')
            )
        return d

    links = {}
    for link in feed.feed.get('links', []):
        links[link['rel']] = link['href']

    return {
        'url': url,
        'next': links.get('next') or links.get('prev-archive'),
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


async def route_parse(request):
    if 'url' not in request.query:
        raise web.HTTPBadRequest

    url = request.query['url']

    try:
        if 'outbox' in url:
            data = await parse_activity_stream(url)
        else:
            data = await parse_feed(url)
    except Exception as err:
        logger.warning(f'{url}: {err}')
        raise web.HTTPInternalServerError from err

    body = json.dumps(data, sort_keys=True)
    return web.Response(body=body, content_type='application/json')


def route_index(request):
    with open(BASE_DIR / 'index.html') as fh:
        return web.Response(body=fh.read(), content_type='text/html')


def route_config(request):
    body = json.dumps({'urls': URLS}, sort_keys=True)
    return web.Response(body=body, content_type='application/json')


def parse_config(path):
    urls = []
    with open(path) as fh:
        for line in fh:
            url = line.strip()
            if url and not url.startswith('#'):
                urls.append(url)
    return urls


def get_config(args, name='.plutopluto.cfg'):
    local_config = Path(name)
    home_config = Path.home() / name

    if args.urls:
        return args.urls
    elif args.config:
        return parse_config(args.config)
    elif local_config.exists():
        return parse_config(local_config)
    elif home_config.exists():
        return parse_config(home_config)
    else:
        return []


def main():
    parser = argparse.ArgumentParser(description='simple feed aggregator')
    parser.add_argument('--version', '-V', action='version', version=__version__)
    parser.add_argument('-c', '--config', metavar='FILE', type=Path)
    parser.add_argument('urls', metavar='URL', nargs='*',
        help='full feed url, optionally with a {page} placeholder')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()

    global URLS
    URLS = get_config(args)
    if not URLS:
        logger.error('Error: No urls provided')
        parser.print_usage()
        sys.exit(1)

    app = web.Application()
    app.router.add_static('/static', BASE_DIR / 'static')
    app.router.add_route('GET', '', route_index)
    app.router.add_route('GET', '/parse', route_parse)
    app.router.add_route('GET', '/config', route_config)
    web.run_app(app, host='localhost', port=args.port)


if __name__ == '__main__':
    main()
