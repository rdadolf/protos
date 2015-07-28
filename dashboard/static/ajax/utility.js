function flash_error(type, message) {
  $('#flash_frame').prepend('<div class="alert alert-danger"><button type="button" class="close" data-dismiss="alert">&times;</button><strong>Error: '+type+'</strong> '+message+'</div>');
}

