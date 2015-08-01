// Code shamelessly taken from http://www.abeautifulsite.net/whipping-file-inputs-into-shape-with-bootstrap-3/
"use strict";

$(document).on('change', '.btn-file :file', function() {
  var input = $(this);
  var numFiles = input.get(0).files ? input.get(0).files.length : 1;
  var label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
  input.trigger('fileselect', [numFiles, label]);
});

$(document).on('fileselect', '.btn-file :file', function() {
  var input = $(this).parents('.input-group').find(':text');
});

$(document).ready( function() {
  $('.btn-file :file').on('fileselect', function(event, numFiles, label) {
    var input = $(this).parents('.input-group').find(':text');
    label = (numFiles > 1) ? (numFiles + ' files selected') : label;
    if(input.length) {
      input.val(label);
    }
  });
});
