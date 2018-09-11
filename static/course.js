
var show_subtables = true;
var course = null;
var holes = null;
var games = null;
var course_par = null;

function par_class(throws, par) {
  if (throws != null) {
    return 'par' + (throws - par);
  }
  else {
    return '';
  }
}

function build_result_table_head(holes) {
  var row_values = ['Date', 'Player'];
  for (var i = 0; i < holes.length; i++) {
    var hole = holes[i];
    course_par += hole.par;
    row_values.push({value: hole.hole, class: 'sorttable_numeric'});
  }
  row_values.push({value: 'Sum', class: 'sorttable_numeric'});
  row_values.push({value: 'Par', class: 'sorttable_numeric'});
  append_row('result_head', row_values, null, false, true);
  sorttable.makeSortable(document.getElementById('results_table'));
}

function approach_puts(approach, puts) {
  if (approach == null) approach = '-';
  if (puts == null) puts = '-';
  return ' (' + approach + '/' + puts + ')';
}

function build_results_table() {
  var rules = get_select_value('rule_set_select');
  hide('rulesToggleable');
  show('rules' + rules);
  var table = document.getElementById('tbody');
  table.innerHTML = '';
  for (var i = 0; i < games.length; i++) {
    var game = games[i];
    if ((rules == 0 && game.rules == null) || game.rules == rules) {
      for (var j = 0; j < game.players.length; j++) {
        var row_values = [game.start_time + ' #' + game.game_of_day];
        var row_sum = 0;
        var row_par = 0;
        var player = game.players[j];
        row_values.push(player.name);
        for (var k = 0; k < player.results.length; k++) {
          var result = player.results[k];
          if (player.full) {
            row_sum += result.throws;
          }
          if (result.throws != null) {
            row_par += result.throws - holes[k].par;
          }
          var value = '';
          if (result.throws != null) {
            value = result.throws + '*'.repeat(result.penalty);
          }
          if (result.approaches != null || result.puts != null) {
            value += approach_puts(result.approaches, result.puts);
          }
          var cell_values = {
            value: value,
            class: par_class(result.throws, holes[k].par),
            custom_key: result.throws
          }
          if (result.throws == null) {
            cell_values['custom_key'] = 100;
          }
          row_values.push(cell_values);
        }
        if (player.full) {
          row_values.push(row_sum);
        }
        else {
          row_values.push({value: '', custom_key: row_par + 1000});
        }
        if (player.full) {
          row_values.push({value: row_par, custom_key: row_par});
        }
        else {
          row_values.push({value: '(' + row_par + ')', custom_key: row_par});
        }

        var rules = 0;
        if (game.rules != null) rules = game.rules;
        append_row(table, row_values);
      }
    }
  }
  filter();
}


function handle_results(json) {
  games = json.games;
  build_results_table();
}


function filter() {
  var date_filter = document.getElementById("date_filter").value;
  var player_filter = document.getElementById("player_filter").value.toLowerCase();
  var table = document.getElementById("tbody");
  var filtered_rows = [];
  var exact_matchin = true;
  if (player_filter.endsWith(" ")) {
    exact_matchin = false;
    player_filter = player_filter.substring(0,player_filter.length-1);
  }

  // Filter
  for (var i = 0; i < table.rows.length; i++) {
    if (exact_matchin) {
      var not_filtered = (
        (table.rows[i].cells[0].innerHTML.replace(/\s+/g, '').toLowerCase().indexOf(date_filter) == 0 || date_filter == "") &&
        (table.rows[i].cells[1].innerHTML.toLowerCase() == player_filter || player_filter == ""));
    }
    else {
      var not_filtered = (
        (table.rows[i].cells[0].innerHTML.replace(/\s+/g, '').toLowerCase().indexOf(date_filter) == 0 || date_filter == "") &&
        (table.rows[i].cells[1].innerHTML.toLowerCase().indexOf(player_filter) == 0 || player_filter == ""));
    }
    if (not_filtered){
      table.rows[i].hidden = false;
      for (var k = 0; k < holes.length; k++) {
        if (filtered_rows[k] == null) {
          filtered_rows[k] = [];
        }
        var throws = parseInt(table.rows[i].cells[k + 2].innerHTML);
        if (!isNaN(throws)) filtered_rows[k].push(throws);
      }
    }
    else {
      table.rows[i].hidden = true;
    }
  }

  var avg_row = document.getElementById("avg_row");
  var min_row = document.getElementById("min_row");
  var mode_row = document.getElementById("mode_row");
  var median_row = document.getElementById("median_row");
  var avg_sum = 0;
  var mode_sum = 0;
  var median_sum = 0;
  var min_sum = 0;
  for (var i = 0; i < holes.length; i++) {
    filtered_rows[i].sort();
    var valuesOnRow = filtered_rows[i].length;
    var avg = filtered_rows[i].reduce(function(a, b) { return a + b; }, 0).toFixed(2);
    avg_row.cells[i + 2].innerHTML = (avg/valuesOnRow).toFixed(2);
    avg_row.cells[i + 2].style.backgroundColor = sliding_par_color(avg/valuesOnRow - holes[i].par);
    avg_sum += avg/valuesOnRow;
    var median = filtered_rows[i][Math.floor(filtered_rows[i].length/2)];
    median_row.cells[i + 2].innerHTML = median;
    median_row.cells[i + 2].className = "par"+(median - holes[i].par);
    median_sum += median;
    var mod = mode(filtered_rows[i]);
    mode_row.cells[i + 2].innerHTML = mod;
    mode_row.cells[i + 2].className = "par"+(mod - holes[i].par);
    mode_sum += mod;
    var min = Math.min(...filtered_rows[i]);
    min_row.cells[i + 2].innerHTML = min;
    min_row.cells[i + 2].className = "par"+(min - holes[i].par);
    min_sum += min;
  }
  min_row.cells[holes.length + 2].innerHTML = min_sum;
  min_row.cells[holes.length + 3].innerHTML = min_sum - course_par;
  avg_row.cells[holes.length + 2].innerHTML = avg_sum.toFixed(2);
  avg_row.cells[holes.length + 3].innerHTML = (avg_sum - course_par).toFixed(2);
  avg_row.cells[holes.length + 3].style.backgroundColor = sliding_par_color((avg_sum - course_par)/course.holes);
  mode_row.cells[holes.length + 2].innerHTML = mode_sum;
  mode_row.cells[holes.length + 3].innerHTML = mode_sum - course_par;
  median_row.cells[holes.length + 2].innerHTML = median_sum;
  median_row.cells[holes.length + 3].innerHTML = median_sum - course_par;
}
