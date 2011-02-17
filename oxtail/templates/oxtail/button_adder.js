var submit = document.getElementById('oxtail-submit');
if (!submit) {
    var userArea = document.getElementById('guser').childNodes[0];
    userArea.innerHTML = userArea.innerHTML + ' | <span id=\'oxtail-div\'><input type=\'button\' id=\'oxtail-submit\' value=\'Activate Oxtail\' /></span>';
}
