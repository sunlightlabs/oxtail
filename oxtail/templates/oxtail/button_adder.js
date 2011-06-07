var submit = document.getElementById('oxtail-submit');
if (!submit) {
    var userArea = document.getElementsByClassName('GcwpPb-MEmzyf')[0].childNodes[0];
    userOffset = userArea.parentNode.id == 'guser' ? 40 : -28;
    userArea.innerHTML = userArea.innerHTML + '&nbsp; <span id=\'oxtail-div\' style=\'position: relative\'><button id=\'oxtail-submit\' style=\'background: none repeat scroll 0% 0% transparent; border: 0; padding: 0; margin: 0; width: 166px; height: 34px; position: absolute; left: -166px; top: ' + userOffset + 'px; cursor: pointer;\'><img id=\'oxtail-submit-img\' src=\'{{ host }}{{ oxtail_media_path }}/img/button-off.png\' style=\'position: absolute; left: 0px; clip: rect(0px,166px,34px,0px);\' /></button></span>';
    
    var initialOffset = window.globalStorage === undefined ? 0 : -17;
}
