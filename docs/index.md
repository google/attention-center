---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: home
---
<div class="slidecontainer">
<input id="percentRange" type="range" min="0" max="1000" value="500">
</div><p id="demo"></p>
<br>
<img id="partial_image"/>

<script>
var slider = document.getElementById("percentRange");
var output = document.getElementById("demo");
output.innerHTML = slider.value;

slider.oninput = function() {
  var percentage = this.value

output.innerHTML = percentage/10 +"%"

var xhr = new XMLHttpRequest();
var orig_img = document.querySelector( "#orig" );
xhr.open( "GET", "https://github.com/mo271/mo271.github.io/raw/master/jxl/group_order_test/chestnut_water.jpg", true );
xhr.responseType = "arraybuffer";
xhr.onload = function( e ) {
    var arrayBufferView = new Uint8Array( this.response );
    var partialImage = new Blob( [ arrayBufferView.slice(0, arrayBufferView.length *percentage/1000 ) ], { type: "image/jpeg" } );
    var urlCreator = window.URL || window.webkitURL;
    var img = document.querySelector( "#partial_image" );
    img.src = urlCreator.createObjectURL( partialImage );
};

xhr.send();

}
</script>

