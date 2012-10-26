var submit = document.getElementById('oxtail-submit');
if (submit) {
    var initialOffset = window.globalStorage === undefined ? 0 : -12;
    var submitImg = document.getElementById('oxtail-submit-img');
    
    submitImg.style.top = initialOffset + 'px';
    
    submit.onmouseover = function() {
        submitImg.style.clip = 'rect(25px,49px,51px,0px)';
        submitImg.style.top = (initialOffset - 25) + 'px';
    };
    submit.onmouseout = function() {
        submitImg.style.clip = 'rect(0px,49px,25px,0px)';
        submitImg.style.top = initialOffset + 'px';
    };
    
    submit.onclick = (function() {
        if (window.poligraftParser) {
            window.poligraftParser.fetchData();
        } else {
            var s = document.createElement('script');
            s.setAttribute('src', '{{ host }}{{ oxtail_path }}/oxtail.js');
            s.setAttribute('type', 'text/javascript');
            submit.parentNode.appendChild(s);
            document.defaultView.window.poligraftEnabled = true;
        }
    });
    submit.removeAttribute('disabled');
}

if (window.poligraftParser) {
    window.poligraftParser.loadPage();
}
