var submit = document.getElementById('oxtail-submit');
if (submit) {
    var initialOffset = window.globalStorage === undefined ? 0 : -17;
    var submitImg = document.getElementById('oxtail-submit-img');
    
    submitImg.style.top = initialOffset + 'px';
    
    submit.onmouseover = function() {
        submitImg.style.clip = 'rect(34px,166px,68px,0px)';
        submitImg.style.top = (initialOffset - 34) + 'px';
    };
    submit.onmouseout = function() {
        submitImg.style.clip = 'rect(0px,166px,34px,0px)';
        submitImg.style.top = initialOffset + 'px';
    };
    
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
