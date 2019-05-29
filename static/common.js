
function ajax_post(url, dataHandler, data) {
  $.ajax({
    type: "POST",
    url: url,
    success: dataHandler,
    data: data,
    error: function(x, t, m) {
      console.log(x, t, m);
      set_loading_message("Error: failed to load the data");
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
      set_loading_message("Error: failed to load the data");
    }
  });
}


function post_object(url, object, callback) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url, true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4 && xhr.status === 200) {
      callback();
    }
    else {
      console.log(xhr);
    }
  };
  xhr.send(JSON.stringify(object));
}

function set_loading_message(msg) {
  let loading_msg_p = document.getElementById("loading_message");
  if (loading_msg_p != null) loading_msg_p.innerHTML = msg;
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

function hide(class_name) {
  let elements = document.getElementsByClassName(class_name);
  for (var i = 0; i < elements.length; i++) {
    let element = elements[i];
    element.hidden = true;
  }
}

function show(class_name) {
  let elements = document.getElementsByClassName(class_name);
  for (var i = 0; i < elements.length; i++) {
    let element = elements[i];
    element.hidden = false;
  }
}

function set_html(element, value) {
  if (typeof element == 'string') element = document.getElementById(element);
  element.innerHTML = value;
}


function set_value(element, value) {
  if (typeof element == 'string') element = document.getElementById(element);
  if (value == null) value = "";
  element.value = value;
}



function append_row(table, row_data, row_class, hidden, header) {
  if (typeof table === 'string') {
    table = document.getElementById(table);
  }
  var row = table.insertRow(-1);
  if (row_class != undefined && row_class != null) {
    row.className = row_class;
  }
  if (hidden != undefined && hidden != null) {
    row.hidden = hidden;
  }
  for (var i = 0; i < row_data.length; i++) {
    if (header !== undefined && header) {
      var cell = document.createElement('th');
      row.appendChild(cell);
    }
    else {
      var cell = row.insertCell(-1);
    }
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
      if (cell_data.class != undefined) {
        cell.className = cell_data.class;
      }
      if (cell_data.hidden != undefined) {
        cell.hidden= cell_data.hidden;
      }
      if (cell_data.custom_key != undefined) {
        cell.setAttribute('sorttable_customkey', cell_data.custom_key);
      }
      if (cell_data.onclick != undefined) {
        cell.addEventListener("click", cell_data.onclick);
        if (cell_data.onclick_arg != undefined) {
          cell.setAttribute('onclick_arg', cell_data.onclick_arg);
        }
      }
    }
    else {
      cell.innerHTML = cell_data;
    }
  }
}

function get_select_value(select) {
  if (typeof select === 'string') {
    select = document.getElementById(select);
  }
  return select.options[select.selectedIndex].value;
}

function toggle_selector(select_id, options, common_class, prefix, onchange) {
  let selector = document.getElementById(select_id);
  for (var i = 0; i < options.length; i++) {
    let option_values = options[i];
    let option = document.createElement('option');
    option.innerHTML = option_values.name;
    option.value = option_values.value;
    selector.appendChild(option);
  }
  if (onchange === undefined) {
    selector.onchange = function(){
      hide(common_class);
      show(prefix + selector.value);
    };
  }
  else {
    selector.onchange = onchange;
  }
}

function rule_set_selector(course_id) {
  ajax_get('/data/course/' + course_id + '/rule_sets/', fill_selector);
  function fill_selector(json) {
    var options = [];
    for (var i = 0; i < json.rule_sets.length; i++) {
      var rule_set = json.rule_sets[i];
      var name = rule_set.name + ' (' + rule_set.games + ')';
      options.push({name: name, value: rule_set.id})
    }
    toggle_selector('rule_set_select', options, 'rulesToggleable', 'rules', build_results_table);
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

function mode(array) {
  if(array.length == 0)
      return null;
  var modeMap = {};
  var maxEl = array[0], maxCount = 1;
  for(var i = 0; i < array.length; i++) {
    var el = array[i];
    if(modeMap[el] == null)
        modeMap[el] = 1;
    else
        modeMap[el]++;

    if(modeMap[el] > maxCount || (modeMap[el] >= maxCount && el > maxEl)) {
        maxEl = el;
        maxCount = modeMap[el];
    }
  }
  return maxEl;
}

const PAR_COLORING_RGB = {
  '-2': [0, 102, 255],
  '-1': [0, 255, 0],
  '0': [0, 153, 51],
  '1': [255, 255, 0],
  '2': [255, 153, 51],
  '3': [255, 0, 0],
  '4': [204, 0, 153],
  '5': [255, 153, 187],
  '6': [0, 0, 0],
}

function sliding_par_color(par) {
  if (par > 6) {
    return "#000000";
  }
  else {
    let low = Math.floor(par);
    let high = Math.ceil(par);
    let point = (par - low)/(high - low);
    let low_rgb = PAR_COLORING_RGB[low.toString()];
    if (low == high) {
      return 'rgb(' + low_rgb.join(',') + ')';
    }
    let high_rgb = PAR_COLORING_RGB[high.toString()];
    let r = low_rgb[0] + point*(high_rgb[0] - low_rgb[0]);
    let g = low_rgb[1] + point*(high_rgb[1] - low_rgb[1]);
    let b = low_rgb[2] + point*(high_rgb[2] - low_rgb[2]);
    return "rgb("+Math.round(r)+','+Math.round(g)+','+Math.round(b)+')';
  }
}