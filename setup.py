#!/usr/bin/env python

from setuptools import setup
from distutils.command.build import build
from setuptools.command.install_lib import install_lib


setup(
	name='plutopluto',
	version='1.1.0',
	description="simple feed aggregator",
	long_description=open('README.rst').read(),
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
