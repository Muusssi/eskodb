
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

function ajax_get(url, dataHandler) {
  $.ajax({
    type: "GET",
    url: url,
    success: dataHandler,
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
  var row_data = values;
  for (var i = 0; i < row_data.length; i++) {
    var cell = row.insertCell(-1);
    var cell_data = row_data[i];
    if (cell_data != null && typeof cell_data === 'object') {
      if (cell_data.url != undefined) {
        let link = document.createElement('a');
        link.href = cell_data.url;
        link.innerHTML = cell_data.value;
        cell.appendChild(link);
      }
      else {
        cell.innerHTML = cell_data.value;
      }
      if (cell_data.custom_key != undefined) {
        cell.setAttribute('sorttable_customkey', cell_data.custom_key);
      }
    }
    else {
      cell.innerHTML = cell_data;
    }
  }
}


function course_rating(holes, length, par) {
  if (length == null || length < 100) {
    return '';
  }
  if (holes <= 6) {
    return 'D';
  }
  else if (holes < 18) {
    if (length/holes > 100) return 'BB';
    else if (length/holes > 75) return 'B';
    else return 'C';
  }
  else {
    if (length/holes > 140 && par >= 64) {
      return 'AAA';
    }
    else if (length/holes > 100 && par >= 58) {
      return 'AA';
    }
    else {
      return 'A';
    }
  }
  return 'error';
}

function course_rating_ordering(rating) {
  if (rating == 'AAA') return '1';
  if (rating == 'AA') return '2';
  if (rating == 'A') return '3';
  if (rating == 'BB') return '4';
  if (rating == 'B') return '5';
  if (rating == 'C') return '6';
  if (rating == 'D') return '7';
  if (rating == '') return '10';
  if (rating == 'error') return '100';
}

