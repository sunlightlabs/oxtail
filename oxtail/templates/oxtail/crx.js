var doc = document;
var oxtailInterval = setInterval(function() {
    var frame = doc.getElementById('canvas_frame');
    if (frame && frame.contentDocument) {
        var document = frame.contentDocument;
        if (document.getElementsByClassName('w-as0').length) {
            clearInterval(oxtailInterval);
            {% include 'oxtail/button_adder.js' %}
            
            var loader = document.createElement('script');
            loader.setAttribute('type', 'text/javascript');
            loader.src = 'data:text/javascript;charset=utf-8,' + encodeURIComponent("{% filter escapejs %}{% include 'oxtail/loader.js' %}{% endfilter %}");
            document.getElementsByTagName('head')[0].appendChild(loader);
        }
    }
}, 250);
