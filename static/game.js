var finished = false;


function build_result_table() {

  var table_head = document.getElementById("result_head");

  var header_row = ['Player'];
  var par_row = ['par'];
  var total_par = 0;
  for (var i=0; i<holes.length; i++) {
    var hole = holes[i];
    header_row.push({'value': hole.hole, 'onclick': jump_to_hole_by_click,
                     'onclick_arg': hole.hole});
    par_row.push(hole.par);
    total_par += hole.par;
  }
  header_row.push('Sum');
  header_row.push('par');
  par_row.push(total_par);
  append_row(table_head, header_row, null, false, true);
  append_row(table_head, par_row, null, false, true);
  identify_current_hole();
  update_result_table();
}

function jump_to_hole_by_click() {
  set_current_hole(parseInt(this.getAttribute("onclick_arg")));
}

function update_result_table(json) {
  if (json !== undefined) {
    players = json.results;
  }
  var table = document.getElementById("result_body");
  table.innerHTML = '';
  finished = true;
  for (var i=0; i<players.length; i++) {
    var player = players[i];
    var values = [player.name];
    var sum = 0;
    var par_sum = 0;
    for (var j=0; j<player.results.length; j++) {
      var result = player.results[j];
      var hole = holes[j];
      var par = null;
      if (result.throws != null) {
        sum += result.throws;
        par = result.throws - hole.par;
        par_sum += par;
        var penalties = "";
        for (var p = 0; p < result.penalty; p++) {
          penalties += "*";
        }
        values.push({'value': result.throws.toString() + penalties, 'class': 'par' + par});
      }
      else {
        values.push(result.throws);
        finished = false;
      }

    }
    values.push(sum);
    values.push(par_sum);
    append_row(table, values);
  }
  update_inputs();
}

function publish() {
  ajax_post("/game/" + game.id + "/", update_result_table, $("#results_form").serialize())
  next();
}

function identify_current_hole() {
  for (var j=0; j<holes.length; j++) {
    var played = false;
    for (var i=0; i<players.length; i++) {
      if (players[i].results[j].reported_at != null) {
        played = true;
      }
    }
    if (!played) {
      set_current_hole(holes[j].hole);
      return;
    }
  }
  set_current_hole(1);
}

function set_current_hole(new_hole) {
  var hole_header_row = document.getElementById('result_head').rows[0].cells;
  var hole_data_header_row = document.getElementById('holes_info').rows[0].cells;
  if (current_hole != null) {
    hole_header_row[current_hole].className = "";
    hole_data_header_row[current_hole].className = "";
  }
  current_hole = new_hole;
  hole_header_row[current_hole].className = "par-2";
  hole_data_header_row[current_hole].className = "par-2";
  document.getElementById("current_hole").innerHTML = current_hole;
  update_inputs();
}

function next() {
  if (current_hole < holes.length) {
    set_current_hole(current_hole + 1);
  }
}

function previous() {
  if (current_hole>1) {
    set_current_hole(current_hole - 1);
  }
}

function update_inputs() {
  var btn = document.getElementById("continue_btn");
  if (current_hole == holes.length) {
    btn.disabled = true;
  }
  else {
    btn.disabled = false;
  }
  btn = document.getElementById("previous_btn");
  if (current_hole == 1) {
    btn.disabled = true;
  }
  else {
    btn.disabled = false;
  }

  var rows = document.getElementById('result_body').rows;

  for (var row = 0; row < rows.length; row++) {
    var player = players[row];
    if (player.results[current_hole-1].throws != null) {
      set_value('throws_' + row, player.results[current_hole-1].throws);
      set_value('penalty_' + row, player.results[current_hole-1].penalty);
    }
    else {
      if (player.results[current_hole-1].reported_at == null) {
        set_value('throws_' + row, holes[current_hole-1].par);
      }
      else {
        set_value('throws_' + row, null);
      }
      set_value('penalty_' + row, 0);
    }

    set_value('approaches_' + row, player.results[current_hole-1].approaches);
    set_value('puts_' + row, player.results[current_hole-1].puts);

    var old_avg = "--";
    var old_min = "--";
    var old_min_par = "";
    var old_results = get_previous_results(player.name, holes[current_hole-1].id);
    if (old_results != null) {
      var old_avg = old_results.avg.toFixed(2);
      var old_min = old_results.min;
      old_min_par = "par" + (old_min - holes[current_hole-1].par);
    }
    var old_avg_cell = document.getElementById('previous_avg_'+row);
    var old_min_cell = document.getElementById('previous_min_'+row);
    old_avg_cell.innerHTML = old_avg;
    if (old_avg != '--') {
      old_avg_cell.style.backgroundColor = sliding_par_color(old_avg - holes[current_hole-1].par);
    }
    old_min_cell.innerHTML = old_min;
    old_min_cell.className = old_min_par;
    document.getElementById('result_'+row).value = player.results[current_hole-1].id;
  }
}

function get_previous_results(player_name, hole_id) {
  if (previous_results != null) {
    if (player_name in previous_results && hole_id in previous_results[player_name]) {
      return previous_results[player_name][hole_id];
    }
  }
  return null;
}

function end_game() {
  if (!finished) {
    if (confirm("TULOKSIA PUUTTUU! Haluatko varmasti lopettaa?")) {
      window.location.href = "/game/end/" + game.id + "/?unfinished=true";
    }
  }
  else {
    if (confirm("Haluatko varmasti lopettaa?")) {
      window.location.href = "/game/end/" + game.id + "/?unfinished=false";
    }
  }
};

