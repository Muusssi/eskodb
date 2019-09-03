

function build_hole_input_form(json) {
    holes = json.holes;
    var form = document.getElementById('holes_form');

    for (var i = 0; i < holes.length; i++) {
        var hole = holes[i];

        var header = document.createElement('h3');
        header.innerHTML = hole.hole;
        form.appendChild(header);

        form.appendChild(new_text_input_div("id", hole.id, null, null, null, true));
        form.appendChild(new_text_input_div("par", hole.par, 'par', 'par_input'+hole.hole, '[0-9]'));
        form.appendChild(new_text_input_div("length", hole.length, 'length', 'length_input'+hole.hole, '[0-9]+'));
        form.appendChild(new_text_input_div("height", hole.height, 'height', 'height_input'+hole.hole, '-?[0-9]+'));
        form.appendChild(new_checkbox_div("ob_area", hole.ob_area, 'OB area', 'ob_area_cb'+hole.hole));
        form.appendChild(new_checkbox_div("mando", hole.mando, 'Mando', 'mando_cb'+hole.hole));
        form.appendChild(new_checkbox_div("gate", hole.gate, 'Gate', 'gate_cb'+hole.hole));
        form.appendChild(new_checkbox_div("island", hole.island, 'Island', 'island_cb'+hole.hole));
    }
}

function new_text_input_div(name, value, label, id, pattern, hidden) {
    var div = document.createElement('div');
    if (label != undefined && label != null) {
        var label_elem = document.createElement('label');
        label_elem.innerHTML = label;
        div.appendChild(label_elem);
    }
    var input = document.createElement('input');
    input.type = "text";
    input.name = name;
    input.value = value;
    if (id != undefined && id != null) {
        input.id = id;
    }
    if (pattern != undefined && pattern != null) {
        input.pattern = pattern;
    }
    if (hidden != undefined && hidden != null) {
        div.hidden = hidden;
    }
    div.appendChild(input);
    return div;
}

function new_checkbox_div(name, value, label, id) {
    var div = document.createElement('div');
    if (label != undefined && label != null) {
        var label_elem = document.createElement('label');
        label_elem.innerHTML = label;
        div.appendChild(label_elem);
    }
    var input = document.createElement('input');
    input.type = "text";
    input.name = name;
    input.value = value;
    input.hidden = true;
    div.appendChild(input);

    var cb = document.createElement('input');
    cb.type = "checkbox";
    if (value == true) {
        cb.checked = true;
    }
    else {
        cb.checked = false;
    }
    cb.addEventListener("change", function() {toggle_boolean_input(input)});
    if (id != undefined && id != null) {
        cb.id = id;
    }
    div.appendChild(cb);
    return div;
}

function toggle_boolean_input(element) {
    if (typeof element == 'string') element = document.getElementById(element);
    if (element.value == 'true') {
        element.value = 'false';
    }
    else {
        element.value = 'true';
    }

}