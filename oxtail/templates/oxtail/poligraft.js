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
                parser.threads[hash][index].renderIfAvailable();
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
        
        //Submit to Poligraft
        $.ajax({
            url: '{{ host }}{{ oxtail_path }}/contextualize',
            type: isShort ? 'GET' : 'POST',
            dataType: isShort ? 'jsonp': 'json',
            data: {json: 1, text: text, name: senderName, email: senderAddress},
            success: function(data) {
                var endpoint = '{{ host }}{{ oxtail_path }}/contextualize/' + data.slug + '?callback=?'
                var interval = setInterval(function() {
                    $.getJSON(endpoint, function(realData) {
                        if (realData.all_processed) {
                            origMessage.pgData = realData;
                            origMessage.pgState = 'fetched';
                            clearInterval(interval);
                            if (origMessage.getState() == 'fetched') callback();
                        }
                    })
                }, 2000);
            }
        });
        
        //Get sender information
        /* 
        var sender = this.getSender();
        var senderName = sender.html();
        var senderAddress = sender.attr('email');
        $.ajax({
            url: '{{ host }}{{ oxtail_path }}/person_info.json',
            type: 'GET',
            dataType: 'jsonp',
            data: {name: senderName, email: senderAddress},
            success: function(data) {
                origMessage.senderData = data;
                origMessage.senderState = 'fetched';
                if (origMessage.getState() == 'fetched') callback();
            }
        })
        */
    }
    
    PgMessage.prototype.renderIfAvailable = function() {
        if (this.hash == parent.location.hash) {
            var div = this.getDiv();
            if (this.getState() == 'fetched' && !div.hasClass('pg-rendered') && div.length > 0) {
                //poligraft rendering
                div.removeClass('pg-fetching');
                div.addClass('pg-rendered');
                
                this.remapIfNecessary();
                
                var text = div.html();
                var message = this;
                
                $.each(this.pgData.entities, function(num, entity) {
                    if (!entity.tdata_id) return;
                    var label = message.templates.label(entity);
                    text = text.split(entity.name).join(label);
                })
                div.html(text);
                
                div.find('.pg-wrapper .pg-wrapper').removeClass('.pg-wrapper').find('.pg-insert').remove();
                
                //sender rendering
                var h3 = this.getSender().parent();
                if (this.pgData.organization) {
                    var matches = $.map(this.pgData.entities, function(entity) { if (entity.name == message.pgData.organization) { return entity } else { return null; } })
                    console.log(matches);
                    var org = $('<span class="pg-org"> of ' + (matches.length ? message.templates.label(matches[0]) : message.pgData.organization) + '</span>');
                    h3.append(org);
                }
                h3.parents('.iw').css('overflow', 'visible')
                
                div.find('.pg-wrapper').add(h3.find('.pg-wrapper')).hover(function() {
                    $(this).children('.pg-insert').show();
                }, function() {
                    $(this).children('.pg-insert').hide();
                })
                
            } else if (this.getState() == 'fetching' && !div.hasClass('pg-fetching') && div.length > 0) {
                div.addClass('pg-fetching');
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
        label: _.template("{% filter escapejs %}{% include 'oxtail/item_label.mt.html' %}{% endfilter %}")
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
    
    // On first run, we're on a message, so we can go ahead and run
    window.poligraftParser.loadPage();
    window.poligraftParser.fetchData();
    
    // Unless we're using rapportive, rerun on hash change
    if (!$('oxtail-div').hasClass('oxtail-rapportive')) {
        parent.onhashchange = function() {
            window.poligraftParser.loadPage();
        };
    }
})(jQuery);