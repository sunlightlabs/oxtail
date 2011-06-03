var submit = document.getElementById('oxtail-submit');
if (!submit) {
    var userArea = document.getElementsByClassName('GcwpPb-MEmzyf')[0].childNodes[0];
    userArea.innerHTML = userArea.innerHTML + '&nbsp; <span id=\'oxtail-div\' style=\'position: relative\'><button id=\'oxtail-submit\' style=\'background: none repeat scroll 0% 0% transparent; border: 0; padding: 0; margin: 0; width: 166px; height: 34px; position: absolute; left: -166px; top: -28px; cursor: pointer;\'><img id=\'oxtail-submit-img\' src=\'{{ host }}{{ oxtail_media_path }}/img/button-off.png\' style=\'position: absolute; left: 0px; clip: rect(0px,166px,34px,0px);\' /></button></span>';
    
    var initialOffset = window.globalStorage === undefined ? 0 : -17;
    
    var submitButton = document.getElementById('oxtail-submit');
    var submitImg = document.getElementById('oxtail-submit-img');
    
    submitImg.style.top = initialOffset + 'px';
    
    submitButton.onmouseover = function() {
        submitImg.style.clip = 'rect(34px,166px,68px,0px)';
        submitImg.style.top = (initalOffset - 34) + 'px';
    };
    submitButton.onmouseout = function() {
        submitImg.style.clip = 'rect(0px,166px,34px,0px)';
        submitImg.style.top = initialOffset + 'px';
    };
}
