---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: default
---
<input type="file" />
<form action="#">
      <label for="lang">or select demo image</label>
      <select name="images" id="image_selection">
        <option value="chestnut_water_small.jxl">Chestnut water</option>
        <option value="chestnut_water.jxl">Chestnut water (large)</option>
        <option value="slug_small.jxl">Slug</option>
        <option value="slug.jxl">Slug (large)</option>
        <option value="tree_small.jxl">Tree</option>
        <option value="tree.jxl">Tree (large)</option>
        <option value="petrus_small.jxl">Petrus</option>
        <option value="petrus.jxl">Petrus (large)</option>
        <option value="watch_small.jxl">Watch</option>
        <option value="watch.jxl">Watch (large)</option>
        <option id="custom_option" style="display:none" value="">custom file</option>
      </select>
</form>

<div class="slidecontainer">
<input id="percentRange" type="range" min="10" max="1000" value="250">
</div><p>When <span id="demo"></span> of the bytes of the image are loaded the image will look like this:</p>

<img id="partial_image" alt="For JPEG XL files, this demo currently only works with Chromium derived browsers. If you can't see an image here, you might need to enable decoding of JPEG XL files via a flag in Chrome: go to chrome://flags/ and search for 'jxl'."/>

<script>
const slider = document.getElementById("percentRange");
const output = document.getElementById("demo");
const image_selection = document.getElementById("image_selection");
const file_upload = document.querySelector('input[type=file]');
const custom_option = document.getElementById("custom_option");

let url = "{{ site.baseurl }}/assets/images/" + image_selection.value

function updateImageSource() {
  const xhr = new XMLHttpRequest();
  output.innerHTML = slider.value/10 +"%"
  xhr.open( "GET", url, true );
  xhr.responseType = "arraybuffer";

  xhr.addEventListener("load", () => {
    const arrayBufferView = new Uint8Array( xhr.response );
    const partialImage = new Blob( [ arrayBufferView.slice(0, arrayBufferView.length * slider.value/1000 ) ], { type: "image/jxl" } );
    const urlCreator = window.URL || window.webkitURL;
    const img = document.querySelector( "#partial_image" );
    img.src = urlCreator.createObjectURL( partialImage );
  });
  xhr.send();
}

image_selection.addEventListener("change", () => {
  file_upload.value = "";
  url = "{{ site.baseurl  }}/assets/images/" + image_selection.value
  custom_option.style.display = "none";
  updateImageSource();
});

file_upload.addEventListener("change", () => {
  const reader = new FileReader();
  file = file_upload.files[0];
  reader.addEventListener("load", () => {
    url = reader.result;
    custom_option.style.display = "inline";
    image_selection.value=""
    custom_option.innerText = file_upload.files[0].name;
    updateImageSource();
  }, false);
  reader.readAsDataURL(file_upload.files[0]);
});

slider.addEventListener("change", updateImageSource );

updateImageSource();
</script>

