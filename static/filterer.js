
var table;
var filter_inputs = [];

function filter() {
  for (var i = 2; i < table.rows.length; i++) {
    var row = table.rows[i];
    row.hidden = false;
    for (var j = 0; j < row.cells.length; j++) {
      var cell = row.cells[j];
      var filter_value = filter_inputs[j].value.toLowerCase();
      if (filter_value != "") {
        if (cell.innerHTML.replace(/\s+/g, '').toLowerCase().indexOf(filter_value) < 0) {
          row.hidden = true;
          break;
        }
      }
    }
  }
}

function add_filters(table_id) {
  table = document.getElementById(table_id);
  var headers = table.rows[0].cells;
  var filter_row = table.insertRow(0);
  for (var i = 0; i < headers.length; i++) {
    var header = headers[i];
    var filter_cell = filter_row.insertCell(-1);
    var input = document.createElement('input');
    filter_inputs.push(input);
    input.addEventListener("input", filter);
    filter_cell.appendChild(input);
  }
}
