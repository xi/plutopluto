"use strict";

var $ = function(query) {
	var ob = {};

	if (query == document || query.ELEMENT_NODE) {
		ob.target = query;
	} else if (query.trim()[0] === '<') {
		var div = document.createElement('div');
		div.innerHTML = query;
		ob.target = div.children[0];
	} else {
		ob.target = document.querySelector(query);
	}

	ob.on = function(ev, handler) {
		ob.target.addEventListener(ev, handler);
	};
	ob.ready = function(handler) {
		ob.target.addEventListener('DOMContentLoaded', handler);
	};
	ob.click = function(handler) {
		ob.target.addEventListener('click', handler);
	};
	ob.html = function(value) {
		if (typeof value !== 'undefined') {
			ob.target.innerHTML = value;
		} else {
			return ob.target.innerHTML;
		}
	};
	ob.children = function() {
		return ob.target.children;
	};
	ob.append = function(element) {
		ob.target.appendChild(element.target);
	};
	ob.replace = function(element) {
		ob.target.parentNode.replaceChild(element.target, ob.target);
	}

	return ob;
};

$.ajax = function(url, settings) {
	if (settings.hasOwnProperty('data')) {
		var pairs = [];
		for (var key in settings.data) {
			var value = settings.data[key];
			pairs.push(encodeURIComponent(key) + '=' + encodeURIComponent(value));
		}
		url += '?' + pairs.join('&');
	}

	var request = new XMLHttpRequest();
	request.open('GET', url, true);
	request.onload = function() {
		if (this.status >= 199 && this.status < 400){
			settings.success(JSON.parse(this.response));
		}
	};
	request.send();
};
