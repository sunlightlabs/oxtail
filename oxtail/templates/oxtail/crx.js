var doc = document;
var oxtailInterval = setInterval(function() {
    var frame = doc.getElementById('canvas_frame');
    if (frame && frame.contentDocument) {
        var document = frame.contentDocument;
        if (document.getElementById('guser')) {
            clearInterval(oxtailInterval);
            {% include 'oxtail/button_adder.js' %}
            {% include 'oxtail/loader.js' %}
        }
    }
}, 250);
