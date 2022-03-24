# Attention center

This repository contains
 - a [TensorFlow Lite](https://www.tensorflow.org/lite) model to that can be used to prediect the attention center of an image, i.e. the area where the most salient parts of an image lie.
 - a python script that can be used to batch encode images using the attention centers. This can be used with the submodule [libjxl](firschinghttps://github.com/libjxl/libjxl) in order to create JPEG XL images such that decoing the image will start from the attention center determinend by the model.

 [Using Saliency in progressive JPEG XL images](https://opensource.googleblog.com/2021/09/using-saliency-in-progressive-jpeg-xl-images.html) is a blog post about this open source project.

 For the training of the model [center.tflite](./model/center.tflite) has been trained with images from the [Common objects in context](https://cocodataset.org/#home) annotated with saliency from the [salicon dataset](http://salicon.net/).

## How to use

1. Clone it from GitHub including the submodules
2. Build libjxl, for example by following the [instructions](https://github.com/libjxl/libjxl/blob/main/README.md) given in the the [libjxl repo](https://github.com/libjxl/libjxl).
3. run the `encode_with_centers.py` script.

Here `${INPUT_IMAGE_DIR}` contains images that can be opened with the [Python Imaging Library](https://github.com/python-pillow/Pillow) and `${OUTPUT_IMAGE_DIR}` will be created if it does not exist and the encoded JPEG_XL images will be placed there.

``` shell
git clone https://github.com/google/attention-center --recursive --shallow-submodules
cd libjxl
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF ..
cmake --build . -- -j$(nproc)
cd ../../
python encode_with_centers.py --lite_model_file=./model/center.tflite \
  --image_dir="${INPUT_IMAGE_DIR}" --output_dir="${OUTPUT_IMAGE_DIR}"
```

There are the following flags:
```shell
  --encoder: Location of th encoder binary.
    (default: './libjxl/build/tools/cjxl_ng')
  --image_dir: Filename of a test image.
  --lite_model_file: Path to the corresponding TFLite model.
  --new_suffix: File extension of the compressed file.
    (default: 'jxl')
  --output_dir: Filename of a test image.
  --: everyting after will be handed to the encoder
  ```
An example for using `--` would be
```shell
python encode_with_centers.py --lite_model_file=./model/center.tflite   --image_dir=/tmp/images --output_dir=/tmp/out/ -- -distance 1.1
```
Here the we pass the flag `--distance 1.1` two `cjxl_ng`.

The flags and arguments for `--center_x`, `--center_y` and `--group-order 1` are automatically injected.

