
function function_name(url, handler) {
  $.ajax({
    url: url,
    dataType: 'application/json',
    complete: function(data){
        alert(data)
    },
    success: function(data){
        handler(data)
    }
  });
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

