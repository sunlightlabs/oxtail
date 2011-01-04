/**
 * windowName transport plugin 1.0.0 for jQuery
 *
 * Thanks to Kris Zyp <http://www.sitepen.com/blog/2008/07/22/windowname-transport/>
 * for the original idea and some code. Original BSD license below.
 *
 * Licensed under GPLv3: http://www.gnu.org/licenses/gpl-3.0.txt
 * @author Marko Mrdjenovic <jquery@friedcellcollective.net>
 *
**/
/*
 Copyright (c) 2004-2008, The Dojo Foundation
 All Rights Reserved.

 Licensed under the Academic Free License version 2.1 or above OR the
 modified BSD license. For more information on Dojo licensing, see:

 http://dojotoolkit.org/license
*/
(function ($) {
	$ = $ || window.jQuery;
	var origAjax = $.ajax, idx = 0,
		rurl = /^(\w+:)?\/\/([^\/?#]+)/,
		xhr_wnJSON = function (s) {
			return function () {
				var url = '',
					type = (s.type || '').toUpperCase(),
					frameName = '',
					defaultName = 'jQuery.windowName.transport.frame',
					frame = null, form = null, cleantmr = null,
					u = {};
				function cleanup() {
					cleanTimeout(cleantmr);
					try {
						delete window.jQueryWindowName[frameName];
					} catch (er) {
						window.jQueryWindowName[frameName] = function () {};
					}
					setTimeout(function () {
						$(frame).remove();
						$(form).remove();
					}, 100);
				}
				function setData() {
					try {
						var data = frame.contentWindow.name;
						if (typeof data === 'string') {
							if (data === defaultName) {
								u.status = 501;
								u.statusText = 'Not Implemented';
							} else {
								u.status = 200;
								u.statusText = 'OK';
								u.responseText = data;
							}
							u.readyState = 4; // we are done now
							u.onreadystatechange();
							cleanup();
						}
					} catch (er) {}
				}
				function queryToObject(q) {
					var r = {},
						d = decodeURIComponent;
					$.each(q.split("&"), function (k, v) {
						if (v.length) {
							var parts = v.split('='),
								n = d(parts.shift()),
								curr = r[n];
							v = d(parts.join('='));
							if (typeof curr === 'undefined') {
								r[n] = v;
							} else {
								if (curr.constructor === Array) {
									r[n].push(v);
								} else {
									r[n] = [curr].concat(v);
								}
							}
						}
					});
					return r;
				}
				u = {
					abort: function () {
						cleanup();
					},
					getAllResponseHeaders: function () {
						return '';
					},
					getResponseHeader: function (key) {
						return '';
					},
					open: function (m, u) {
						url = u;
						this.readyState = 1;
						this.onreadystatechange();
					},
					send: function (data) {
						data = data || '';
						if (data.indexOf('windowname=') < 0) { // tell the server we want windowname transport
							data += (data === ''? '' : '&') + 'windowname=' + (s.windowname || 'true');
						}
						// prepare frame
						frameName = "jQueryWindowName" + ('' + Math.random()).substr(2, 8);
						window.jQueryWindowName = window.jQueryWindowName || {};
						window.jQueryWindowName[frameName] = function () {};
						var fmethod = null, faction = null, ftarget = null, fsubmit = null,
							local = window.location.href.substr(0, window.location.href.indexOf('/', 8)),
							locallist = ['/robots.txt', '/crossdomain.xml'];
						form = document.createElement('form');
						if ($.browser.msie) {
							try {
								frame = document.createElement('<iframe name="' + frameName + '" onload="jQueryWindowName[\'' + frameName + '\']()">');
								$('body')[0].appendChild(frame);
							} catch (er) {
							}
						}
						if (!frame) {
							frame = document.createElement('iframe');
						}
						frame.style.display = 'none';
						window.jQueryWindowName[frameName] = frame.onload = function (interval) {
							function get_local(next) {
								var file = '';
								if (next) {
									idx += 1;
								}
								file = s.localfile? s.localfile : locallist[idx]? local + locallist[idx] : null;
								if (!file) {
									file = window.location.href;
								}
								return file;
							}
							function is_local() {
								var c = false;
								try {
									c = !!frame.contentWindow.location.href;
									// try to get location - if we can we're still local and have to wait some more...
								} catch (er) {
									// if we're at foreign location we're sure we can proceed
								}
								return c;
							}
							try {
								if (frame.contentWindow.location.href === 'about:blank') {
									return;
								}
							} catch (er) {}
							if (u.readyState === 3) {
								if (is_local()) {
									setData();
									if (u.status === 200) {
										$.ajaxSettings.wnJSONsupported[s.url] = true;
									}
								} else { // if not local try other local
									frame.contentWindow.location = get_local(true);
								}
							}
							if (u.readyState === 2 && (s.windowname || !is_local())) {
								u.readyState = 3;
								u.onreadystatechange();
								frame.contentWindow.location = get_local();
							}
						};
						cleantmr = setTimeout(function () { // stop after 2 mins
							cleanup();
						}, 120000);
						frame.name = frameName;
						frame.id = frameName;
						if (!frame.parentNode) {
							$('body')[0].appendChild(frame);
						}
						if (type === 'GET') {
							frame.contentWindow.location.href = url + (url.indexOf('?') >= 0? '&' : '?') + data;
						} else {
							// prepare form
							form.style.display = 'none';
							$('body')[0].appendChild(form);
							// make references to the proper stuff
							fmethod = form.method;
							faction = form.action;
							ftarget = form.target;
							fsubmit = form.submit;
							form.method = 'POST';
							form.action = url;
							form.target = frameName;
							$.each(queryToObject(data.replace(/\+/g, '%20')), function (k, v) {
								function setVal(k, v) {
									var input = document.createElement("input");
									input.type = 'hidden';
									input.name = k;
									input.value = v;
									form.appendChild(input);
								}
								if (v.constuctor === Array) {
									$.each(v, function (i, v) {
										setVal(k, v);
									});
								} else {
									setVal(k, v);
								}
							});
							try {
								fmethod = form.method = 'POST';
								faction = form.action = url;
								ftarget = form.target = frameName;
							} catch (er2) {}
							frame.contentWindow.location = 'about:blank'; // opera likes this
							try {
								fsubmit();
							} catch (er3) {
								fsubmit.call(form);
							}
						}
						this.readyState = 2;
						this.onreadystatechange();
						if (frame.contentWindow) {
							frame.contentWindow.name = defaultName;
						}
					},
					setRequestHeader: function (key, value) {},
					onreadystatechange: function () {},
					readyState: 0,
					responseText: '',
					responseXML: null,
					status: null,
					statusText: null
				};
				return u;
			};
		},
		xhr_CORS = window.XDomainRequest ? // use XDomainRequest if available (ie) or default XMLHttpRequest
			function () {
				var xhr = new window.XDomainRequest();
				// need to fake stuff that XDomainRequest doesn't provide (http://msdn.microsoft.com/en-us/library/cc288060(VS.85).aspx)
				xhr.onreadystatechange = function () {};
				xhr.setRequestHeader = function (key, value) {};
				xhr.getAllResponseHeaders = function () {
					return {'content-type': xhr.contentType};
				};
				xhr.getResponseHeader = function (key) {
					if (key === 'content-type') {
						return this.contentType;
					}
				};
				xhr.onload = function () {
					$.extend(xhr, {readyState: 4, status: 200, statusText: 'OK'});
					xhr.onreadystatechange.call(xhr, {});
				};
				xhr.onprogress = function () {
					$.extend(xhr, {readyState: 3, status: 200, statusText: 'OK'});
					xhr.onreadystatechange.call(xhr, {});
				};
				xhr.onerror = function (ev) {
					$.extend(xhr, {readyState: 4, status: 0, statusText: ''});
					xhr.onreadystatechange.call(xhr, {});
				};
				return xhr;
			} : 
			$.ajaxSettings.xhr;
	$.ajaxSettings.wnJSONsupported = {};
	$.ajaxSettings.CORSsupported = {};
	try {
		$.support.CORS = !!window.XDomainRequest || (function () {
			var xhr = $.ajaxSettings.xhr();
			xhr.open('GET', 'http://domain.fake/', true);
			xhr.send(); // this will throw an error on browers that don't support Allow-Origin on XMLHttpRequest
			xhr.abort();
			return true;
		}());
	} catch (er) {
		$.support.CORS = false;
	}
	$.extend({
		ajax: function (s) {
			var parts = rurl.exec(s.url || ''),
				remote = parts && (parts[1] && parts[1] !== window.location.protocol || parts[2] !== window.location.host),
				type = (s.type || '').toUpperCase(),
				origSuccess = s.success || function () {};
			if (s.windowname) {
				s.xhr = xhr_wnJSON(s);
			} else if (type === 'POST' && remote) {
				if ($.support.CORS && $.ajaxSettings.CORSsupported[s.url] !== false) {
					s.xhr = xhr_CORS;
					s.success = function (data, status, xhr) {
						if (xhr.status === 0) {
							status = 'error';
							$.ajaxSettings.CORSsupported[s.url] = false;
							if (this.error) {
								this.error.call(this, s, xhr, status, {name: 'Unsupported', message: 'CORS not supported.'});
							}
						} else {
							$.ajaxSettings.CORSsupported[s.url] = true;
							return origSuccess.apply(this, arguments);
						}
					};
				} else if ($.ajaxSettings.wnJSONsupported[s.url] !== false) {
					s.xhr = xhr_wnJSON(s);
				}
			}
			return origAjax.call(this, s);
		}
	});
}(jQuery));
