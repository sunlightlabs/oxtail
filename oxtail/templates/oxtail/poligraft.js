(function($) {
    var console = parent.console;
    
    // Microtemplates, swiped from underscore
    var _ = {};
    _.templateSettings = {
        evaluate    : /<%([\s\S]+?)%>/g,
        interpolate : /<%=([\s\S]+?)%>/g
    };
    
    _.template = function(str, data) {
        var c  = _.templateSettings;
        var tmpl = 'var __p=[],print=function(){__p.push.apply(__p,arguments);};' +
            'with(obj||{}){__p.push(\'' +
            str.replace(/\\/g, '\\\\')
               .replace(/'/g, "\\'")
               .replace(c.interpolate, function(match, code) {
                   return "'," + code.replace(/\\'/g, "'") + ",'";
               })
               .replace(c.evaluate || null, function(match, code) {
                   return "');" + code.replace(/\\'/g, "'")
                                      .replace(/[\r\n\t]/g, ' ') + "__p.push('";
               })
               .replace(/\r/g, '\\r')
               .replace(/\n/g, '\\n')
               .replace(/\t/g, '\\t')
               + "');}return __p.join('');";
        var func = new Function('obj', tmpl);
        return data ? func(data) : func;
    };
    
    // template formatting stuff
    var template_helpers = {
        'formatDollars': function(number) {
            var out = [], counter = 0, part = true;
            var digits = number.toFixed(0).split("");
            while (part) {
                part = (counter == 0 ? digits.slice(-3) : digits.slice(counter - 3, counter)).join("");
                if (part) {
                    out.unshift(part);
                    counter -= 3;
                }
            }
            return out.join(",");
        },
        'formatDate': function(date) {
            var d = new Date(date);
            return [
                ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][d.getMonth()],
                ' ',
                d.getDate(),
                ', ',
                d.getFullYear()
            ].join("");
        },
        'fixName': function(name) {
            var n = name.split("");
            return n[0] + '$+$+' + n.slice(1).join("");
        },
        'percents': function() {
            var args = Array.prototype.slice.call(arguments);
            var sum = 0;
            $.each(args, function(idx, val) { sum += val; });
            
            return (sum == 0 ? $.map(args, function() { return 0; }) : $.map(args, function(val) { return Math.round(100*val/sum); })).join(',');
        }
    }
    
    var regexpEscape = function(text) {
        return text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&");
    }
    
    // Cache class for storing messages
    var RingCache = function(size) {
        this.dict = {};
        this.buffer = [];
        this.size = size;
        this.position = 0;
    }
    
    RingCache.prototype.set = function(key, value) {
        if (this.dict[key] !== undefined) {
            this.buffer[this.dict[key]].value = value;
            return;
        } else {
            if (this.buffer[this.position] !== undefined) {
                delete this.dict[this.buffer[this.position].key];
            }
            this.buffer[this.position] = {key: key, value: value};
            this.dict[key] = this.position;
            this.position = (this.position + 1) % this.size;
        }
    }
    
    RingCache.prototype.get = function(key, defaultValue) {
        if (this.dict[key] !== undefined) {
            return this.buffer[this.dict[key]].value;
        } else {
            return defaultValue;
        }
    }

    
    // Define all of the boilerplate parsing classes, which only really matter the first time the code gets loaded
    var PgParser = function() {
        this.threads = new RingCache(10);
        this.people = new RingCache(20);
    }
    
    PgParser.prototype.loadPage = function() {
        var hash = parent.location.hash;
        var thread = this.threads.get(hash, {});
        
        var parser = this;
        $(document).find('.Bk').each(function(index, message) {
            var body = $(message).find('.ii.gt>div');
            
            if (thread[index] === undefined) {
                thread[index] = new PgMessage(hash, index);
            }
            
            if (body.length > 0 && !body.eq(0).hasClass('pg-rendered')) {
                thread[index].fetchAndRender();
            }
        })
        this.threads.set(hash, thread);
    }
    
    PgParser.prototype.fetchData = function() {
        var hash = parent.location.hash;
        var parser = this;
        $.each(parser.threads.get(hash), function(index, message) {
            message.fetchAndRender();
        });
    }
    
    var PgMessage = function(hash, index) {
        this.pgState = 'not fetched';
        this.senderState = 'not fetched';
        this.hash = hash;
        this.index = index;
        this.remapped = false;
    }
    
    PgMessage.prototype.getState = function() {
        return this.pgState;
    }
    
    PgMessage.prototype.getDiv = function() {
        return $(document).find('.Bk').eq(this.index).find('.ii.gt>div').eq(0);
    }
    
    PgMessage.prototype.getSender = function() {
        return this.getDiv().parent().parent().children('.gE.iv.gt').find('span.gD[email]');
    }
    
    PgMessage.prototype.fetch = function(callback) {
        if (this.getState() == 'fetched') {
            callback();
            return;
        }
        
        var div = this.getDiv();
        if (div.length == 0) return;
        var text = div.html();
        var origMessage = this;
        this.pgState = 'fetching';
        
        //Determine URL and method
        var encodedText = encodeURIComponent(text);
        var isShort = text.length < 2000;
        
        //Get sender information
        var sender = this.getSender();
        var senderName = sender.html();
        var senderAddress = sender.attr('email');
        
        this.senderName = senderName;
        this.senderAddress = senderAddress;
        
        //Submit to Poligraft
        $.ajax({
            url: '{{ host }}{{ oxtail_path }}/contextualize',
            type: isShort ? 'GET' : 'POST',
            dataType: isShort ? 'jsonp': 'json',
            data: {json: 1, text: text},
            success: function(realData) {
                origMessage.pgData = realData;
                origMessage.pgState = 'fetched';
                callback();
            }
        });
        
        //Get sender information, if necessary, otherwise use cached
        var sender = this.getSender();
        var senderName = sender.html();
        var senderAddress = sender.attr('email');
        var senderId = senderName + '_' + senderAddress
        var senderData = window.poligraftParser.people.get(senderId)
        if (senderData) {
            origMessage.senderData = senderData;
            origMessage.senderState = 'fetched';
            callback();
        } else {
            $.ajax({
                url: '{{ host }}{{ oxtail_path }}/sender_info',
                type: 'GET',
                dataType: 'jsonp',
                data: {name: senderName, email: senderAddress},
                success: function(data) {
                    // add to cache
                    window.poligraftParser.people.set(senderId, data);
                    
                    // do callback
                    origMessage.senderData = data;
                    origMessage.senderState = 'fetched';
                    callback();
                }
            })
        }
    }
    
    // non-message-specific helper function for rendering messages
    var fixPanel = function(pgPanel) {
        var idxs = [];
        var ids = [];
        pgPanel.find('.pg-panel-item').each(function(idx, node) {
            var $node = $(node);
            idxs[idxs.length] = parseInt($node.attr('data-pg-pos'));
            ids[ids.length] = $node.attr('data-pg-id');
        }).show();
        idxs.sort(function(a,b) { return a - b });
        $.each(idxs, function(n, idx) {
            var node = pgPanel.find('div[data-pg-pos=' + idx + ']');
            pgPanel.append(node);
        })
        $.each(ids, function(n, id) {
            var nodes = pgPanel.find('div[data-pg-id=' + id + ']');
            if (nodes.length > 1) {
                nodes.slice(1).hide();
            }
        })
        
        // do the expanding and collapsing
        var items = pgPanel.find('.pg-panel-item:visible');
        items.eq(0).removeClass('pg-collapsed').show();
        items.slice(1).addClass('pg-collapsed').find('.pg-panel-content').hide();
        
        items.find('.sender-header').unbind('click').bind('click', function() {
            var parent = $(this).parent();
            if (parent.hasClass('pg-collapsed')) {
                parent.removeClass('pg-collapsed').find('.pg-panel-content').slideDown('fast');
            } else {
                parent.addClass('pg-collapsed').find('.pg-panel-content').slideUp('fast');
            }
        })
    }
    
    PgMessage.prototype.renderIfAvailable = function() {
        if (this.hash == parent.location.hash) {
            var div = this.getDiv();
            if (this.getState() == 'fetched' && !div.hasClass('pg-rendered') && div.length > 0) {
                //poligraft rendering
                div.removeClass('pg-fetching');
                div.addClass('pg-rendered');
                
                this.remapIfNecessary();
                
                //do the replacing
                var text = div.html();
                var message = this;
                
                var match_strings = [];
                var match_labels = {};
                var popups = [];
                $.each(this.pgData.entities, function(num, entity) {
                    popups[num] = $('<div>').addClass('pg-insert').html(
                        message.templates.org_info($.extend({}, template_helpers, entity.entity_data))
                    ).attr('data-pg-idx', num);

                    for (var i = 0; i < entity.matched_text.length; i++) {
                        if (entity.matched_text[i] != entity.entity_data.slug) {
                            var label = message.templates.label($.extend({}, template_helpers, entity.entity_data, {'match_name': entity.matched_text[i], 'idx': num}));
                            match_strings.push(regexpEscape(entity.matched_text[i]));
                            match_labels[entity.matched_text[i]] = label;
                        }
                    }
                })
                
                var text_split = text.split(RegExp('(' + match_strings.join('|') + ')(?![^<>]*?>)'));
                for (var i = 1; i < text_split.length; i += 2) {
                    text_split[i] = match_labels[text_split[i]];
                }
                text = text_split.join("");
                
                div.html(text);
                
                div.find('.pg-wrapper .pg-wrapper').removeClass('.pg-wrapper').find('.pg-insert').remove();
                
                div.find('.pg-wrapper').each(function() {
                    var idx = parseInt($(this).attr('data-pg-idx'));
                    
                    var showing = false;
                    var timeout = null;
                    
                    var hoverOver = function() {
                        if (!showing) {
                            var $this = $(this);                        
                            $(document.body).append(popups[idx]);
                            var offset = $this.offset();
                            popups[idx].css({'left': offset.left + 'px', 'top': (offset.top + $this.height()) + 'px'}).fadeIn('fast');
                            showing = true;
                            
                            popups[idx].unbind('hover').hover(hoverOver, hoverOut);
                        }
                        clearTimeout(timeout);
                    }
                    var hoverOut = function() {
                        timeout = setTimeout(function() {
                            popups[idx].fadeOut('fast', function() {
                                $(this).remove();
                                showing = false;
                            });
                        }, 250);
                    };
                    $(this).hover(hoverOver, hoverOut);
                })
                
            } else if (this.pgState == 'fetching' && !div.hasClass('pg-fetching') && div.length > 0) {
                div.addClass('pg-fetching');
            }
            
            var senderParent = this.getSender().parent();
            if (this.senderState == 'fetched' && !senderParent.hasClass('pg-sender-rendered') && senderParent.length > 0) {
                senderParent.addClass('pg-sender-rendered');
                
                //sender rendering
                var h3 = senderParent;
                var senderText = '';
                var senderId = this.senderData.name + '_' + this.senderData.email;
                if (this.senderData.organization) {
                    senderText += '<span class="pg-org"> of <span class="pg-highlighted" data-pg-id="' + senderId + '">' + this.senderData.organization + '</span></span>';
                    
                }
                
                if (this.senderData.name) {                    
                    this.getSender().hide();
                    senderText = '<span class="pg-sender"><span class="pg-highlighted" data-pg-id="' + senderId + '">' + this.senderData.name + '</span></span>' + senderText;
                }
                    
                var senderEl = $(senderText);
                this.getSender().after(senderEl);
                                
                h3.find('.pg-org .pg-highlighted').hover(function() {
                    $(document).find('.pg-panel-item[data-pg-id=' + $(this).attr('data-pg-id') + ']').addClass('pg-indicate-org');
                }, function() {
                    $(document).find('.pg-panel-item[data-pg-id=' + $(this).attr('data-pg-id') + ']').removeClass('pg-indicate-org');
                })
                
                h3.find('.pg-sender .pg-highlighted').hover(function() {
                    $(document).find('.pg-panel-item[data-pg-id=' + $(this).attr('data-pg-id') + ']').addClass('pg-indicate-sender');
                }, function() {
                    $(document).find('.pg-panel-item[data-pg-id=' + $(this).attr('data-pg-id') + ']').removeClass('pg-indicate-sender');
                })
                
                var pgPanel = $(document).find('.pg-panel');
                if (pgPanel.length == 0) {
                    var sidePanel = $(document).find('.Bs > tr > td.Bu').eq(2).children('.nH').eq(0).children('.nH').eq(0);
                    pgPanel = $(this.templates.sender_sidebar({}));
                    sidePanel.children('.nH').eq(0).after(pgPanel);
                    
                    pgPanel.delegate("a", "click", function() {
                        window.open($(this).attr('href'));
                        return false;
                    })
                }
                
                pgPanel.append(this.templates.sender_sidebar_item($.extend({}, template_helpers, this.senderData, {'position': this.index, 'templates': this.templates})));
                fixPanel(pgPanel);
            }
        }
    }
    
    PgMessage.prototype.fetchAndRender = function() {
        var origMessage = this;
        this.fetch(function(div) {
            origMessage.renderIfAvailable();
        });
        origMessage.renderIfAvailable();
    }
    
    PgMessage.prototype.remapIfNecessary = function() {
        this.remapped = true;
        return;
        
        // not running the remapping for now, since we're not doing aggregates using the new system
        if (this.remapped) return;
        var message = this;
        $.each(this.pgData.entities, function(num, entity) {
            if (entity.contributors.length != 0 && entity.tdata_type == 'politician') {
                $.each(entity.contributors, function(cnum, contributor) {
                    var origContributor = $.map(message.pgData.entities, function(element) { return element.tdata_id == contributor.tdata_id ? element : null; })[0];
                    origContributor.contributors.push({tdata_name: entity.tdata_name, tdata_id: entity.tdata_id, tdata_type: entity.tdata_type, tdata_slug: entity.tdata_slug, amount: contributor.amount})
                });
            }
        });
        this.remapped = true;
    }
    
    var enableIncludes = function(tmpl) {
        return function(data) {
            return tmpl.call(data, $.extend(data, {'templates': PgMessage.prototype.templates}))
        }
    }
    
    PgMessage.prototype.templates = {
        label: enableIncludes(_.template("{% filter escapejs %}{% spaceless %}{% include 'oxtail/item_popup.mt.html' %}{% endspaceless %}{% endfilter %}")),
        sender_sidebar: _.template("{% filter escapejs %}{% spaceless %}{% include 'oxtail/sender_sidebar.mt.html' %}{% endspaceless %}{% endfilter %}"),
        sender_sidebar_item: enableIncludes(_.template("{% filter escapejs %}{% spaceless %}{% include 'oxtail/sender_sidebar_item.mt.html' %}{% endspaceless %}{% endfilter %}")),
        org_info: _.template("{% filter escapejs %}{% spaceless %}{% include 'oxtail/org_info.mt.html' %}{% endspaceless %}{% endfilter %}")
    }
    
    
    // Check to see if the Poligraft class has already been loaded and, if not, load it
    if (window.poligraftParser === undefined) {
        window.poligraftParser = new PgParser();
    }
    
    // Check to see whether or not the stylesheet as been loaded, and, if not, load it.
    var sheets = $(document.documentElement).find('head').find('link[rel=stylesheet]').map(function() { return $(this).attr('href'); });
    var stylesLoaded = false;
    $.each(sheets, function(index, sheet) {
        if (sheet.indexOf('poligraft-rapportive.css') != -1) {
            stylesLoaded = true;
        }
    })
    if (!stylesLoaded) {
        $(document.documentElement).find('head').append('<link rel="stylesheet" type="text/css" href="{{ host }}{{ oxtail_media_path }}/css/poligraft-rapportive.css?cb={{ oxtail_git_rev }}" />')
    }
        
    var enablePoligraft = function() {
        var bound = null;
        var run = function() {
            window.poligraftParser.loadPage();
            
            clearInterval(bound);
            bound = setInterval(function() {
                window.poligraftParser.loadPage();
            }, 1000);
        };
        
        run();
        
        // Unless we're using rapportive, rerun on hash change
        if (!$('oxtail-div').hasClass('oxtail-rapportive')) {
            parent.onhashchange = run;
        }
        var button = $(document).find('#oxtail-submit').attr('value', 'Disable Inbox Influence');
        button.get(0).onclick = null;
        button.unbind('click').bind('click', function() {
            window.poligraftEnabled = false;
            parent.onhashchange = null;
            clearInterval(bound);
            button.attr('value', 'Enable Inbox Influence').unbind('click').bind('click', enablePoligraft);
        })
    }
    
    if (window.poligraftEnabled) {
        enablePoligraft();
    }
})(jQuery);
