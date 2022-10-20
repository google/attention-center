---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: home
---
<input type="file" /><br />

<form action="#">
      <label for="lang">Image</label>
      <select name="images" id="image_selection">
        <option value="two_chestnuts.jxl">Two Chestnuts</option>
        <option value="slug.jxl">Slug</option>
        <option value="harpsichord.jxl">Harpsichord</option>
        <option value="petrus.jxl">Petrus</option>
        <option value="chestnut_water.jxl">Chestnut water</option>
      </select>
</form>

<div class="slidecontainer">
<input id="percentRange" type="range" min="0" max="1000" value="500">
</div><p id="demo"></p>
<br>

<!-- <img id="hidden_image" src="https://github.com/mo271/mo271.github.io/raw/master/jxl/group_order_test/chestnut_water.jpg"/> -->
<img id="partial_image"/>

<script>
const slider = document.getElementById("percentRange");
const output = document.getElementById("demo");
const image_selection = document.getElementById("image_selection");
output.innerHTML = slider.value;
const img = document.querySelector( "#partial_image" );
const reader = new FileReader();
console.log(image_selection.value);
var xhr = new XMLHttpRequest();
var file = ""

function updateImageSource(url, percentage) {
    xhr.open( "GET", url, true );
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

image_selection.addEventListener("change", () => {
  console.log("changing selection");
  file = "";
  document.querySelector('input[type=file]').value = "";
  }
);

slider.oninput = function() {
  var percentage = this.value
  output.innerHTML = percentage/10 +"%"
  file = document.querySelector('input[type=file]').files[0];
  reader.addEventListener("load", () => {
    // convert image file to base64 string
    const result = reader.result;
    //console.log(result.substring(result.indexOf('base64') + 8, 100));
    updateImageSource(result, percentage);
  }, false);

  if (file) {
    reader.readAsDataURL(file);
  } else {
    const url = "{{ site.baseurl  }}/assets/images/" + image_selection.value
    updateImageSource(url, percentage);
  }

}
</script>

