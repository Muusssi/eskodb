var scaleing = 4;
const ANCHOR_SIZE = 20;

var anchors = [{type: 'anchor', x: 0, y: 30}, {type: 'anchor', x: 0, y: 70}];
anchors.push({type: 'hole', x: 0, y: 100});
var map_items = [];
var selected_point = null;
var basket_x = 0;
var basket_y = 100;
var debug_length_estimate = false;
var hole = null;
var course = null;

function handleMapData(json) {
  if (json.anchors.length > 0) {
    anchors = json.anchors;
    update();
  }

}

function handleHoleData(json) {
  hole = json;
  course_id = get_url_parameter('course');
  for (var i = 0; i < hole.included_in_courses.length; i++) {
    if (hole.included_in_courses[i].id == int(course_id)) {
      course = hole.included_in_courses[i];
      set_html('hole_num', course.name + ' ' + course.holes + ': #' + course.hole_number);
      break;
    }
  }
  set_html('official_length', hole.length);

}

function setup() {
  createCanvas(600, 500);
  update();
}


function draw() {}

function post_map() {
  post_object('/data/hole/'+ hole.id + '/map/', {'items': anchors}, move_to_course_page);
  function move_to_course_page() {
    if (course != null) {
      window.location = '/course/' + course.id + '/';
    }
    else {
      window.location = '/';
    }
  }
}

function update() {
  redraw_map();
  set_html('estimated_length', estimate_length().toFixed(0));
}

function redraw_map() {
  background(230);
  grid();
  draw_map_items();
  draw_anchors();
  draw_fairway();
}

function mousePressed() {
  move();
}

function mouseDragged() {
  if (selected_point != null) {
    anchors[selected_point].x = xp(mouseX);
    anchors[selected_point].y = yp(mouseY);
    update();
  }
}

function draw_anchors() {
  fill(50, 50, 255);
  for (var i = 0; i < anchors.length; i++) {
    var point = anchors[i];
    if (point.type == 'hole') {
      noFill();
      ellipse(px(point.x), py(point.y), scaleing*20, scaleing*20);
      fill(255, 255, 0);

    }
    ellipse(px(point.x), py(point.y), ANCHOR_SIZE, ANCHOR_SIZE);
  }
  stroke(0, 0, 200);
  line(px(0), py(0), px(anchors[0].x), py(anchors[0].y));
  line(px(anchors[1].x), py(anchors[1].y), px(anchors[2].x), py(anchors[2].y));
}

function grid() {
  stroke(0);
  noFill();
  strokeWeight(2);
  ellipse(width/2, height, scaleing*50*2, scaleing*50*2);
  ellipse(width/2, height, scaleing*100*2, scaleing*100*2);
  ellipse(width/2, height, scaleing*150*2, scaleing*150*2);
  ellipse(width/2, height, scaleing*200*2, scaleing*200*2);
  ellipse(width/2, height, scaleing*250*2, scaleing*250*2);
  line(width/2, 0, width/2, height);
  stroke(50);
  strokeWeight(1);
  ellipse(width/2, height, scaleing*25*2, scaleing*25*2);
  ellipse(width/2, height, scaleing*75*2, scaleing*75*2);
  ellipse(width/2, height, scaleing*125*2, scaleing*125*2);
  ellipse(width/2, height, scaleing*175*2, scaleing*175*2);
  ellipse(width/2, height, scaleing*225*2, scaleing*225*2);
  fill(0);
  rect(width/2 - 10, height - 10, 20, 20);
}

function draw_map_items() {
  for (var i = 0; i < map_items.length; i++) {
    var item = map_items[i];
    if (item.type == 'tree') {

    }
    else if (item.type == 'mando') {

    }
    else if (item.type == 'rock') {

    }
  }
}


function move() {
  for (var i = 0; i < anchors.length; i++) {
    var point = anchors[i];
    if (dist(px(point.x), py(point.y), mouseX, mouseY) <= ANCHOR_SIZE*2) {
      selected_point = i;
      return;
    }
  }
  selected_point = null;
}

function draw_fairway() {
  noFill();
  strokeWeight(5);
  stroke(200, 0, 0);
  bezier(px(0), py(0),
         px(anchors[0].x), py(anchors[0].y),
         px(anchors[1].x), py(anchors[1].y),
         px(anchors[2].x), py(anchors[2].y));
}

function estimate_length() {
  stroke(0, 0, 200);
  strokeWeight(1);
  var prev_estimate = 0;
  var estimate = 100;
  var prev_points = [{x: 0, y: 0}];
  for (var i = 0; i < anchors.length; i++) {
    prev_points.push({x: anchors[i].x, y: anchors[i].y});
  }
  while (abs(estimate - prev_estimate) > 5) {
    prev_estimate = estimate
    estimate = 0;
    var points = [{x: 0, y: 0}];
    for (var i = 1; i < prev_points.length; i++) {
      points.push({x: (prev_points[i].x + prev_points[i-1].x)/2, y: (prev_points[i].y + prev_points[i-1].y)/2});
    }
    points.push({x: prev_points[prev_points.length - 1].x, y: prev_points[prev_points.length - 1].y});
    if (debug_length_estimate) ellipse(px(points[0].x), py(points[0].y), 5, 5);
    for (var i = 1; i < points.length; i++) {
      if (debug_length_estimate) {
        ellipse(px(points[i].x), py(points[i].y), 5, 5);
        line(px(points[i].x), py(points[i].y), px(points[i-1].x), py(points[i-1].y));
      }
      var d = dist(points[i].x, points[i].y, points[i-1].x, points[i-1].y);
      estimate += d;
    }
    estimate = (prev_estimate + estimate)/2;
    if (points.length > 8) return estimate;
    prev_points = points;
  }
  return estimate;
}

function zoom_in() {
  scaleing *= 1.2;
  redraw_map();
}

function zoom_out() {
  scaleing *= 0.8;
  redraw_map();
}


function px(x) {
  return x*scaleing + width/2;
}
function py(y) {
  return height - y*scaleing;
}
function xp(x) {
  return (x - width/2)/scaleing;
}
function yp(y) {
  return (height - y)/scaleing;
}
