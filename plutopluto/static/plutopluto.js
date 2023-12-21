var template = document.querySelector('template');
var stream = document.querySelector('#stream');
var loading = document.querySelector('.loading');

var locked = function(fn) {
	var lock = false;
	return async function() {
		if (!lock) {
			lock = true;
			await fn();
			lock = false;
		}
	};
};

var formatDate = function(text) {
	var date = new Date(parseInt(text, 10) * 1000);
	var format = 'YYYY-MM-dd hh:mm';

	var o = {
		'Y': date.getFullYear(),
		'M': date.getMonth() + 1,
		'd': date.getDate(),
		'h': date.getHours(),
		'm': date.getMinutes(),
		's': date.getSeconds,
	};

	for (var key in o) {
		if (new RegExp('(' + key + '+)').test(format)) {
			var value = o[key].toString();
			if (RegExp.$1.length > 1) {
				value = ('0000' + value).substr(-RegExp.$1.length);
			}
			format = format.replace(RegExp.$1, value);
		}
	}

	return format;
};

var bottomDistance = function() {
	var doc = document.body.scrollHeight;
	var screen = window.innerHeight;
	var position = document.body.scrollTop || window.scrollY;
	return doc - position - screen;
};

var escapeHTML = function(text) {
	var p = document.createElement('p');
	p.textContent = text;
	return p.innerHTML;
};

var appendEntries = function(entries) {
	entries.forEach(entry => {
		var li = document.createElement('li');
		li.className = 'post';
		li.innerHTML = template.innerHTML
			.replaceAll('{{source}}', escapeHTML(entry.source))
			.replaceAll('{{source_link}}', escapeHTML(entry.source_link))
			.replaceAll('{{feed_link}}', escapeHTML(entry.feed_link))
			.replaceAll('{{link}}', escapeHTML(entry.link))
			.replaceAll('{{title}}', escapeHTML(entry.title))
			.replaceAll('{{dt}}', escapeHTML(formatDate(entry.dt)))
			.replaceAll('{{{content}}}', entry.content);
		stream.append(li);
	});
};

var fetchJSON = async function(url) {
	var r = await fetch(url);
	if (r.ok) {
		return r.json();
	} else {
		throw r;
	}
};

var getInitialUrls = async function() {
	var q = new URLSearchParams(location.search);
	var urls = q.getAll('url');
	if (urls.length) {
		return urls;
	} else {
		var config = await fetchJSON('/config');
		return config.urls;
	}
};

var page = 0;
var next = [];
var entries = [];

var loadNextPage = async function() {
	var current = next;
	next = [];

	await Promise.allSettled(current.map(async raw => {
		var url = raw.replace('{page}', page);
		var feed = await fetchJSON('/parse?' + new URLSearchParams({url: url}));

		if (feed.next) {
			next.push(feed.next);
		} else if (raw.includes('{page}')) {
			next.push(raw);
		}

		feed.entries.forEach(entry => {
			entry.feed_link = '/?' + new URLSearchParams({url: raw});
			entries.push(entry);
		});
	}));

	entries.sort((a, b) => b.dt - a.dt);
	page++;
};

var renderMore = locked(async function() {
	if (entries.length === 0) {
		await loadNextPage();
	}
	if (entries.length === 0) {
		loading.hidden = true;
		return;
	}
	appendEntries(entries.splice(0, 10));
	if (entries.length < 30) {
		await loadNextPage();
	}
});

var main = async function() {
	next = await getInitialUrls();

	document.addEventListener('scroll', () => {
		if (bottomDistance() < 4000) {
			renderMore();
		}
	}, {passive: true});

	loading.addEventListener('click', renderMore);

	// load initial content
	renderMore();
};

main();
