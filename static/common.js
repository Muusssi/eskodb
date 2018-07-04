
function ajax_post(url, dataHandler, data) {
  $.ajax({
    type: "POST",
    url: url,
    success: dataHandler,
    data: data,
    error: function(x, t, m) {
      console.log(x, t, m);
      document.getElementById("loading_message").innerHTML = "Error: failed to load the data"
    }
  });
}

function toggle_by_id(element_id) {
  let element = document.getElementById(element_id);
  element.hidden = !element.hidden;
}

function toggle(class_name) {
  let elements = document.getElementsByClassName(class_name);
  for (var i = 0; i < elements.length; i++) {
    let element = elements[i];
    element.hidden = !element.hidden;
  }
}


function set_value(element_id, value) {
  document.getElementById(element_id).value = value;
}



function append_row(table_id, values) {
  var table = document.getElementById(table_id);
  var row = table.insertRow(-1);
  var row_data = values[i];

  for (var i = 0; i < row_data.length; i++) {
    var cell = row.insertCell(-1);
    var cell_data = row_data[j];
    if (typeof cell_data === 'object') {

    }
    else {
      cell.innerHTML = cell_data;
    }
  }
}

