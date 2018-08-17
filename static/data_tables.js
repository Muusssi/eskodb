

function game_times_table(course_id) {
  ajax_get('/data/course/' + course_id + '/game_times/', fill_game_times_table);

  function fill_game_times_table(json) {

    for (var rules_id in json) {
      var times = json[rules_id];
      for (var i = 0; i < times.length; i++) {
        let time_object = times[i];
        var values = [
            time_object.pool,
            time_object.min + ' h',
            time_object.avg + ' h',
            time_object.max + ' h',
            time_object.games,
        ];
        var hidden = false;
        if (rules_id != 0) {
            hidden = true;
        }
        append_row('game_times', values, 'rules' + rules_id + ' rulesToggleable' , hidden);
      }
    }
  }
}

function course_data_table(course_data) {
  var holes = course_data.holes_data;
  var title_row = [''];
  var par_row = ['par'];
  var len_row = ['Pituus'];
  var height_row = ['Korkeusero'];
  var ob_row = ['OB'];
  var map_row = [''];
  var par_sum = 0;
  var len_sum = 0;
  for (var i = 0; i < holes.length; i++) {
    var hole = holes[i];
    par_sum += hole.par;
    len_sum += hole.length;
    title_row.push(hole.hole);
    par_row.push(hole.par);
    len_row.push(hole.length);
    height_row.push(hole.height);
    var link = 'Add map';
    if (hole.map) link = 'map';
    map_row.push({value: link, url: '/hole/'+hole.id+'/map/edit'})
    var ob = '';
    if (hole.ob_area) ob += ' ob';
    if (hole.mando) ob += ' mando';
    if (hole.island) ob += ' island';
    ob_row.push(ob);
  }
  title_row.push('');
  par_row.push(par_sum);
  len_row.push(len_sum);
  append_row('holes_info', title_row, '', false, true);
  append_row('holes_info', par_row);
  append_row('holes_info', len_row);
  append_row('holes_info', height_row);
  append_row('holes_info', ob_row);
  append_row('holes_info', map_row);
}
