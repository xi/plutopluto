var template = document.querySelector('template');
var stream = document.querySelector('#stream');
var loading = document.querySelector('.loading');

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
			.replaceAll('{{link}}', escapeHTML(entry.link))
			.replaceAll('{{title}}', escapeHTML(entry.title))
			.replaceAll('{{dt}}', escapeHTML(formatDate(entry.dt)))
			.replaceAll('{{{content}}}', entry.content);
		stream.append(li);
	});
};

var fetchJSON = function(url) {
	return fetch(url).then(r => {
		if (r.ok) {
			return r.json();
		} else {
			throw r;
		}
	});
};

var getConfig = function() {
	var q = new URLSearchParams(location.search);
	var urls = q.getAll('url');
	if (urls.length) {
		return Promise.resolve({'urls': urls});
	} else {
		return fetchJSON('/config');
	}
}

getConfig().then(config => {
	var entries = [];
	var page = 0;

	var loadNextPageLock = false;
	var loadNextPage = function() {
		if (loadNextPageLock) {
			return;
		}

		loadNextPageLock = true;

		var promises = config.urls.map(url => {
			if (url.includes('{page}')) {
				url = url.replace('{page}', page);
			} else if (page !== 0) {
				return;
			}

			return fetchJSON('/parse?' + new URLSearchParams({url: url})).then(data => {
				entries = entries.concat(data.entries);
			});
		});

		Promise.all(promises).finally(() => {
			// now that we have entries, we can show some
			if (stream.children.length === 0) {
				loadMore();
			}

			loadNextPageLock = false;
		});

		page++;
	};

	var loadMore = function() {
		entries.sort((a, b) => {
			return b.dt - a.dt;
		});
		appendEntries(entries.splice(0, 10));
		if (entries.length < 30) {
			loadNextPage();
		}
	};

	document.addEventListener('scroll', () => {
		if (bottomDistance() < 4000) {
			loadMore();
		}
	}, {passive: true});

	loading.addEventListener('click', loadMore);

	// load initial content
	loadNextPage();
});
