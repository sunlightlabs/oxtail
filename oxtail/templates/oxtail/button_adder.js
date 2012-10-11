var submit = document.getElementById('oxtail-submit');
if (!submit) {
    var searchTable = document.querySelectorAll('#gbvg .gbtc')[0];
    var userArea = document.createElement('li');
    userArea.style.display = "inline-block";
    searchTable.insertBefore(userArea, searchTable.childNodes[0]);
    userArea.innerHTML = userArea.innerHTML + '<button id=\'oxtail-submit\' style=\'background: none repeat scroll 0% 0% transparent; border: 0; padding: 0; margin: 0; height: 34px; z-index: 999; cursor: pointer; overflow: hidden;\'><img id=\'oxtail-submit-img\' src=\'{{ host }}{{ oxtail_media_path }}/img/button-off.png\' style=\'position: relative; top: 0px; clip: rect(0px,166px,34px,0px);\' /></button>';
 }
