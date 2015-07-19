"use strict";

$(document).ready(function() {
	$.ajax('/config', {success: function(config) {
		var entries = [];
		var page = 0;

		// load templates
		var template = $('#stream').html();
		Mustache.parse(template);
		$('#stream').html('');

		var formatDate = function(date, format) {
			var o = {
				'Y': date.getFullYear(),
				'M': date.getMonth() + 1,
				'd': date.getDate(),
				'h': date.getHours(),
				'm': date.getMinutes(),
				's': date.getSeconds
			}

			for (var key in o) {
				if (new RegExp('(' + key + '+)').test(format)) {
					var value = o[key].toString();
					if (RegExp.$1.length > 1) {
						value = ("0000" + value).substr(-RegExp.$1.length);
					}
					format = format.replace(RegExp.$1, value)
				}
			}

			return format;
		};

		var formatDateFilter = function() {
			return function(text, render) {
				var dt = new Date(parseInt(render(text), 10) * 1000);
				return formatDate(dt, 'YYYY/MM/dd hh:mm');
			}
		};

		var bottomDistance = function() {
			var doc = document.body.scrollHeight;
			var screen = window.innerHeight;
			var position = document.body.scrollTop;
			return doc - position - screen;
		};

		var appendEntries = function(entries) {
			entries.forEach(function(entry) {
				entry.formatDate = formatDateFilter;
				var rendered = Mustache.render(template, entry);
				$('#stream').append($(rendered));
			});
		};

		var loadNextPageLock = false;
		var loadNextPage = function() {
			if (!loadNextPageLock) {
				loadNextPageLock = true;

				config.urls.forEach(function(url) {
					if (url.indexOf('{page}') >= 0) {
						url = url.replace('{page}', page);
					} else if (page !== 0) {
						return;
					}

					$.ajax('/parse', {
						data: {url: url},
						success: function(data) {
							entries = entries.concat(data.entries);

							// now that we have entries, we can show some
							if ($('#stream').children().length === 0) {
								loadMore();
							}

							// ideally we would wait until all requests have finished
							// but this is only a simple optimisation anyway
							loadNextPageLock = false;
						}
					});
				});
				page++;
			}
		};

		var loadMore = function() {
			entries.sort(function(a, b) {
				return b.dt - a.dt;
			});
			appendEntries(entries.splice(0, 10));
			if (entries.length < 30) {
				loadNextPage();
			}
		};

		$(document).on('scroll', function() {
			if (bottomDistance() < 4000) {
				loadMore();
			}
		});
		$('.loading').click(loadMore);

		// load initial content
		loadNextPage();
	}});

	// youtube video embedding
	$(document).on('click', function(event) {
		if (event.target.alt.match(/^https:\/\/www\.youtube/)) {
			var iframe = $('<iframe class="youtube">');
			iframe.target.src = event.target.alt;
			$(event.target).replace(iframe);
		}
	});
});
