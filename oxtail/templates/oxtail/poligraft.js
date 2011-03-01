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
        }
    }
    
    var regexpEscape = function(text) {
        return text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&");
    }

    
    // Define all of the boilerplate classes, which only really matter the first time the code gets loaded
    var PgParser = function() {
        this.threads = {};
    }
    
    PgParser.prototype.loadPage = function() {
        var hash = parent.location.hash;
        if (this.threads[hash] === undefined) {
            this.threads[hash] = {};
        }
        
        var parser = this;
        $(document).find('.Bk').each(function(index, message) {
            var body = $(message).find('.ii.gt>div');
            
            if (parser.threads[hash][index] === undefined) {
                parser.threads[hash][index] = new PgMessage(hash, index);
            }
            
            if (body.length > 0 && !body.eq(0).hasClass('pg-rendered')) {
                parser.threads[hash][index].fetchAndRender();
            }
        })
    }
    
    PgParser.prototype.fetchData = function() {
        var hash = parent.location.hash;
        var parser = this;
        $.each(parser.threads[hash], function(index, message) {
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
        return $(document).find('.Bk').eq(this.index).find('.ii.gt>div');
    }
    
    PgMessage.prototype.getSender = function() {
        return this.getDiv().parent().parent().children('.gE.iv.gt').find('h3>span[email]');
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
        
        //Get sender information
        var sender = this.getSender();
        var senderName = sender.html();
        var senderAddress = sender.attr('email');
        $.ajax({
            url: '{{ host }}{{ oxtail_path }}/sender_info',
            type: 'GET',
            dataType: 'jsonp',
            data: {name: senderName, email: senderAddress},
            success: function(data) {
                origMessage.senderData = data;
                origMessage.senderState = 'fetched';
                callback();
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
                
                // hack to fix paragraphs
                div.find('p').each(function() {
                    var $this = $(this);
                    var fakeP = $('<div class="pg-fake-paragraph">');
                    fakeP.html($this.html());
                    $this.replaceWith(fakeP);
                })
                
                //do the replacing
                var text = div.html();
                var message = this;
                
                var match_strings = [];
                var match_labels = {};
                $.each(this.pgData.entities, function(num, entity) {
                    for (var i = 0; i < entity.matched_text.length; i++) {
                        if (entity.matched_text[i] != entity.entity_data.slug) {
                            var label = message.templates.label($.extend({}, template_helpers, entity.entity_data, {'match_name': entity.matched_text[i]}));
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
                
                div.find('.pg-wrapper').hover(function() {
                    $(this).children('.pg-insert').show();
                }, function() {
                    $(this).children('.pg-insert').hide();
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
                if (this.senderData.organization) {
                    senderText += '<span class="pg-org"> of ' + (this.senderData.org_info ? this.templates.label($.extend({}, template_helpers, this.senderData.org_info, {'match_name': this.senderData.organization})) : this.senderData.organization) + '</span>';
                    
                }
                
                if (this.senderData.name) {                    
                    this.getSender().hide();
                    senderText = '<span class="pg-sender">' + this.templates.label_simple($.extend({}, template_helpers, this.senderData)) + '</span>' + senderText;
                }
                    
                var senderEl = $(senderText);
                h3.append(senderEl);
                
                h3.parents('.iw').css('overflow', 'visible');
                
                h3.find('.pg-wrapper').hover(function() {
                    $(this).children('.pg-insert').show();
                }, function() {
                    $(this).children('.pg-insert').hide();
                }).find('a').click(function() {
                    window.open($(this).attr('href'));
                    return false;
                })
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
    
    PgMessage.prototype.templates = {
        label: _.template("{% filter escapejs %}{% include 'oxtail/item_label.mt.html' %}{% endfilter %}"),
        label_simple: _.template("{% filter escapejs %}{% include 'oxtail/item_label_simple.mt.html' %}{% endfilter %}")
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
        $(document.documentElement).find('head').append('<link rel="stylesheet" type="text/css" href="{{ host }}{{ oxtail_media_path }}/css/poligraft-rapportive.css" />')
    }
        
    var enablePoligraft = function() {
        var run = function() {
            window.poligraftParser.loadPage();
            
            var captureChanges = function(evt) {
                if (evt.target.className == 'mD') {
                    setTimeout(function() {
                        window.poligraftParser.loadPage();
                    }, 250);
                }
            }
            
            $('.pg-activated').each(function() {
                this.removeEventListener('DOMNodeInserted', captureChanges, false);
            })
            
            $('.nH.hx').each(function() {
                $(this).addClass('pg-activated');
                this.addEventListener("DOMNodeInserted", captureChanges, false);
            });
        };
        
        run();
        
        // Unless we're using rapportive, rerun on hash change
        if (!$('oxtail-div').hasClass('oxtail-rapportive')) {
            parent.onhashchange = run;
        }
        var button = $(document).find('#oxtail-submit').attr('value', 'Deactivate Oxtail');
        button.get(0).onclick = null;
        button.unbind('click').bind('click', function() {
            window.poligraftEnabled = false;
            parent.onhashchange = null;
            button.attr('value', 'Reactivate Oxtail').unbind('click').bind('click', enablePoligraft);
        })
    }
    
    if (window.poligraftEnabled) {
        enablePoligraft();
    }
})(jQuery);