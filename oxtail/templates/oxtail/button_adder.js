var submit = document.getElementById('oxtail-submit');
if (!submit) {
    var searchTable = document.querySelectorAll('.no .nn .oy8Mbf')[0];
    var userArea = document.createElement('td');
    searchTable.childNodes[0].appendChild(userArea);
    userArea.innerHTML = userArea.innerHTML + '<button id=\'oxtail-submit\' style=\'background: none repeat scroll 0% 0% transparent; border: 0; padding: 0; margin: 0; width: 166px; height: 34px; position: absolute; right: 20px; top: 40px; z-index: 999; cursor: pointer;\'><img id=\'oxtail-submit-img\' src=\'{{ host }}{{ oxtail_media_path }}/img/button-off.png\' style=\'position: absolute; left: 0px; clip: rect(0px,166px,34px,0px);\' /></button>';
 }
