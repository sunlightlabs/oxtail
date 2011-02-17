var submit = document.getElementById('oxtail-submit');
if (submit) {
    submit.onclick = (function() {
        if (window.poligraftParser) {
            window.poligraftParser.fetchData();
        } else {
            var s = document.createElement('script');
            s.setAttribute('src', '{{ host }}{{ oxtail_path }}/oxtail.js');
            s.setAttribute('type', 'text/javascript');
            var parent = document.getElementById('oxtail-div');
            parent.appendChild(s);
            document.defaultView.window.poligraftEnabled = true;
        }
    });
    submit.removeAttribute('disabled');
}

if (window.poligraftParser) {
    window.poligraftParser.loadPage();
}
