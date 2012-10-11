var doc = document;
var oxtailInterval = setInterval(function() {
    if (document.getElementById('gbvg')) {
        clearInterval(oxtailInterval);
        {% include 'oxtail/button_adder.js' %}
        
        var loader = document.createElement('script');
        loader.setAttribute('type', 'text/javascript');
        loader.src = 'data:text/javascript;charset=utf-8,' + encodeURIComponent("{% filter escapejs %}{% include 'oxtail/loader.js' %}{% endfilter %}");
        document.getElementsByTagName('head')[0].appendChild(loader);
    }
}, 250);
