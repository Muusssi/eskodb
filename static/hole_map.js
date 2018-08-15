var scale = 3;
const ANCHOR_SIZE = 20;

var anchor_points = [[0,30], [0,70]];
anchor_points.push([0, 100]);
var selected_point = null;
var basket_x = 0;
var basket_y = 100;


function setup() {
  createCanvas(600, 500);
  update_scale();
}


function draw() {
  background(200);
  grid();
  draw_anchor_points();
  draw_fairway();
}

function mousePressed() {
  move();
}

function mouseDragged() {
  if (selected_point != null) {
    anchor_points[selected_point][0] = xp(mouseX);
    anchor_points[selected_point][1] = yp(mouseY);
  }
}

function draw_anchor_points() {
  fill(0);
  for (var i = 0; i < anchor_points.length; i++) {
    if (i == anchor_points.length - 1) {
      fill(255, 255, 0);
    }
    var point = anchor_points[i];
    ellipse(px(point[0]), py(point[1]), ANCHOR_SIZE, ANCHOR_SIZE);
  }
}

function grid() {
  noFill();
  ellipse(width/2, height, scale*50*2, scale*50*2);
  ellipse(width/2, height, scale*100*2, scale*100*2);
  ellipse(width/2, height, scale*150*2, scale*150*2);
  ellipse(width/2, height, scale*200*2, scale*200*2);
  ellipse(width/2, height, scale*250*2, scale*250*2);
  fill(0);
  rect(width/2 - 10, height - 10, 20, 20);
}

function move() {
  for (var i = 0; i < anchor_points.length; i++) {
    var point = anchor_points[i];
    if (dist(px(point[0]), py(point[1]), mouseX, mouseY) <= ANCHOR_SIZE/2) {
      selected_point = i;
      return;
    }
  }
  selected_point = null;
}

function draw_fairway() {
  noFill();
  bezier(px(0), py(0),
         px(anchor_points[0][0]), py(anchor_points[0][1]),
         px(anchor_points[1][0]), py(anchor_points[1][1]),
         px(anchor_points[2][0]), py(anchor_points[2][1]));
}

function update_scale() {
  scale = document.getElementById('scale_input').value;
}


function px(x) {
  return x*scale + width/2;
}
function py(y) {
  return height - y*scale;
}
function xp(x) {
  return (x - width/2)/scale;
}
function yp(y) {
  return (height - y)/scale;
}