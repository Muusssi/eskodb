

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
