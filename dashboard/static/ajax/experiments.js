

/***** Loading experiment list ************************************************/
function get_active_project() {
  return $('#activeProject').val();
}
function get_experiment_mask() {
  return {};
}
function request_experiments() {
  //console.log('Requesting experiments');
  project = get_active_project();
  mask = get_experiment_mask();
  serialized_mask = JSON.stringify(mask);

  // Placeholder while request is going out.
  $('#experiment_list').prepend('<div>Loading...</div>')

  $.ajax({
    dataType: "JSON",
    url: $SCRIPT_ROOT+'/experiment_list',
    data: {'project': project, 'mask': serialized_mask},
    timeout: 5000,
  })
  .done( function(response, stat, xhr) {
    $('#experiment_list').empty();
    $.each(response, function(idx, obj){ add_experiment_to_list(obj);} );
    setup_experiment_callbacks();
  })
  .fail( function(xhr, error_type, error_msg) {
    $('#experiment_list').empty();
    if( xhr.status==0 ) { // Likely a network error
      $('#experiment_list').prepend(alert_box(xhr.status,"Couldn't communicate with server."));
    } else {
      error_detail = $(xhr.responseText).siblings('p').text();
      $('#experiment_list').prepend(alert_box(xhr.status+' '+error_msg, error_detail));
    }
  });
}
function add_experiment_to_list(html) {
  $('#experiment_list').prepend(html);
}

/***** Loading experiment details *********************************************/
// "Active" experiments are ones that are currently visible
function activate_experiment(exp) {
  $(exp).find('div.experiment-detail:first').css('display','block');
}
function deactivate_experiment(exp) {
  $(exp).find('div.experiment-detail:first').css('display','none');
}
function is_experiment_active(exp) {
  disp = $(exp).find('div.experiment-detail:first').css('display');
  return disp=='block';
}

// "Loaded" means the content has been retrieved from the server.
function set_experiment_loaded(exp) {
  $(exp).find('div.experiment-loaded').text(1);
}
function set_experiment_unloaded(exp) {
  $(exp).find('div.experiment-loaded').text(0);
}
function is_experiment_loaded(exp) {
  is_loaded = $(exp).find('div.experiment-loaded').text();
  return is_loaded==1;
}
function load_experiment(exp, xid) {
  details = $(exp).find('div.experiment-detail:first');
  //console.log("loading details for experiment "+xid);
  $.ajax({
    //dataType: "JSON",
    dataType:"HTML",
    url: $SCRIPT_ROOT+'/experiment_info',
    data: {xid: xid, project:get_active_project()},
    timeout: 5000,
  })
  .done( function(response, stat, xhr) {
    details.empty().append(response);
    set_experiment_loaded(exp);
  })
  .fail( function(xhr, error_type, error_msg) {
    if( xhr.status==0 ) { // Likely a network error
      details.empty().append(alert_box(xhr.status,"Couldn't communicate with server."));
    } else {
      error_detail = $(xhr.responseText).siblings('p').text();
      details.empty().append(alert_box(xhr.status+' '+error_msg,error_detail));
    }
  });
}

function handle_experiment_click(ev) {
  exp = ev.delegateTarget;

  if( is_experiment_active(exp) ) {
    deactivate_experiment(exp);
    return false;
  }
  if( !is_experiment_loaded(exp) ) {
    xid = $(exp).children('.experiment-id:first').text();
    load_experiment(exp, xid);
  }
  activate_experiment(exp);
  return false;
}
function setup_experiment_callbacks() {
  $('div.experiment').on('click',handle_experiment_click);
}
