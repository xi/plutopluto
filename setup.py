#!/usr/bin/env python

import os
import re
from setuptools import setup

DIRNAME = os.path.abspath(os.path.dirname(__file__))
rel = lambda *parts: os.path.abspath(os.path.join(DIRNAME, *parts))

README = open(rel('README.rst')).read()
INIT = open(rel('plutopluto', '__init__.py')).read()
VERSION = re.search("__version__ = '([^']+)'", INIT).group(1)


setup(
	name='plutopluto',
	version=VERSION,
	description="simple feed aggregator",
	long_description=README,
	url='https://github.com/xi/plutopluto',
	author='Tobias Bengfort',
	author_email='tobias.bengfort@posteo.de',
	packages=['plutopluto'],
	include_package_data=True,
	install_requires=[
		'argparse',
		'flask',
		'werkzeug',
		'feedparser',
		'beautifulsoup4',
	],
	entry_points={'console_scripts': [
		'plutopluto=plutopluto:main',
	]},
	license='GPLv2+',
	classifiers=[
		'Environment :: Web Environment',
		'Intended Audience :: End Users/Desktop',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: JavaScript',
		'License :: OSI Approved :: GNU General Public License v2 or later '
			'(GPLv2+)',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary',
	])
