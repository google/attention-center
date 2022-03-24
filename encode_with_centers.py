"""
    Copyright 2022 Google LLC

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        https://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.


Tool to compute the attention center of images and encode to jxl using those.

Example command:

python encode_with_centers.py --lite_model_file=./model/center.tflite \
  --image_dir=/tmp/images --output_dir=/tmp/out/
"""

import subprocess

from absl import app
from absl import flags
from absl import logging
import numpy as np
import PIL
import pathlib

import tensorflow as tf


_LITE_MODEL_FILE = flags.DEFINE_string(
    'lite_model_file', None, 'Path to the corresponding TFLite model.')
_IMAGE_DIR = flags.DEFINE_string('image_dir', None,
                                 'Filename of a test image.')
_OUTPUT_DIR = flags.DEFINE_string('output_dir', None,
                                  'Filename of a test image.')
_ENCODER = flags.DEFINE_string('encoder', './libjxl/build/tools/cjxl_ng',
                               'Location of th encoder binary.')
_NEW_SUFFIX = flags.DEFINE_string(
    'new_suffix', 'jxl', 'File extension of the compressed file.')
_DRY_RUN = flags.DEFINE_bool(
    'dry_run', False, 'If true, only do a dry run, does not write files.')
_VERBOSE = flags.DEFINE_bool(
    'verbose', True, 'If true, prints info about the commands executed.')
FLAGS = flags.FLAGS

# image shape in (height, width)
_MODEL_IMAGE_SHAPE = (480, 640)


def load_tflite_model(lite_model_file):
    """Loads a tflite model.

    Args:
        lite_model_file: filename of the model tflite model file.

    Returns:
        The loaded tflite model as interpreter.
    """
    with open(lite_model_file, 'rb') as f:
        tflite_model_content = f.read()
    interpreter = tf.lite.Interpreter(model_content=tflite_model_content)
    interpreter.allocate_tensors()
    return interpreter


def get_lite_map(interpreter):
    """Returns the interpreter's input index-by-name map."""
    return {m['name']: m['index'] for m in interpreter.get_input_details()}


def lite_predict(interpreter, index_map, image_tensor):
    """Makes one inference on an image using the model.

    Args:
        interpreter: a tflite interpreter.
        index_map: a dict mapping names to the interpreter's indices.
        image_tensor: a float [num_rows, num_columns, 3]-numpy.ndarray
            representation of the image

    Returns:
        A vector containing the result of the inference.
    """
    interpreter.set_tensor(index_map['image:0'], image_tensor)
    interpreter.invoke()
    output_details = interpreter.get_output_details()

    return interpreter.get_tensor(output_details[0]['index'])


def tflite_predictions(interpreter, image_tensor):
    """Make one inference on an image using the model."""
    lite_map = get_lite_map(interpreter)
    return lite_predict(interpreter, lite_map, image_tensor)


def to_float(im_np):
    """Converts the image numpy array to floats.

    Args:
        im_np: Image as a numpy array. Either with (some) float dtype and
            value-range [0.0 ... 1.0] or (some) int dtype with value-range
            range(256).

    Returns:
        Image as np.float32 numpy.ndarray with value-range [0.0 ... 1.0].
    """
    if np.issubdtype(im_np.dtype, np.integer):
        return im_np.astype(np.float32) / 255.0
    return im_np.astype(np.float32)


def process_image(image_pil):
    """Reads one image into a numpy array.

    Args:
        image_pil: an :py:class:`~PIL.Image.Image` object.

    Returns:
        A float [num_rows, num_columns, 3]-numpy.ndarray representation of the
        image, or `None` if the file could not be read, or the number of
        indices is not 2 or 3, or 3-index image has a final index range other
        than 3 (RGB) or 4 (RGBA).
    """
    image = np.asarray(image_pil)
    if ((not 2 <= len(image.shape) <= 3) or
            image.shape[2:] not in ((3,), (4,), ())):
        logging.error('Invalid image shape: %r', image.shape)
        return None

    rgb_image = np.asarray(image_pil.convert(
        'RGB')) if image.shape[2:] in ((), (4,)) else image
    return to_float(rgb_image)


def read_one_image(file_name):
    """Reads one image from file into a numpy array.

    Args:
        file_name: The full path of the image file.
        gray: whether the output image needs to be gray.

    Returns:
        A float [num_rows, num_columns, 3]-numpy.ndarray representation of the
        image, or `None` if the file could not be read, or the number of
        indices is not 2 or 3, or 3-index image has a final index range other
        than 3 (RGB) or 4 (RGBA).
    """
    with open(file_name, 'rb') as f:
        image_pil = PIL.Image.open(f)
        if hasattr(PIL.ImageOps, 'exif_transpose'):
            # Applies exif transpose
            image_pil = PIL.ImageOps.exif_transpose(image_pil)
        return process_image(image_pil)


def get_crop_region(padded_shape, original_shape):
    """Finds the non-padding region in the reshaped image.

    Supposed padded_shape is a reshaped image after resizing and padding from
    original_shape.

    Args:
        padded_shape: The shape of resized and padded image.
        original_shape: The shape of the original image.

    Returns:
        The non-padding resion in the reshaped image, in the format of
        [left, top, right, bottom].
    """
    padded_height, padded_width = padded_shape
    original_height, original_width = original_shape

    aspect_ratio_padded = float(padded_height) / float(padded_width)
    aspect_ratio_original = float(original_height) / float(original_width)
    cropped_region = None
    if aspect_ratio_padded > aspect_ratio_original:
        # padding happens for the height
        valid_height = round(padded_width * aspect_ratio_original)
        start = (padded_height - valid_height) // 2
        cropped_region = [0, start, padded_width, valid_height + start - 1]
    elif aspect_ratio_padded < aspect_ratio_original:
        # padding happens for the width
        valid_width = round(padded_height / aspect_ratio_original)
        start = (padded_width - valid_width) // 2
        cropped_region = [start, 0, valid_width + start - 1, padded_height]
    else:
        cropped_region = [0, 0, padded_width, padded_height]
    return cropped_region


# The center is computed with image of model_input_image_shape, needs convert
# the point to the original image with original_resolution.
def convert_center_to_original_resolution(
        center, model_input_image_shape, original_resolution):
    """Rescales the center back to the original solution.

    Args:
        center: A pair of int coordinates, row-indices are always 0th indices.
        model_input_image_shape: A pair of ints. The shape of the resized and
            padded region.
        original_resolution: A pair of ints. The shape of the original image.
    """
    # Original image is resized and padded to the model_input_image_shape.
    # left, top, right, bottom are the bounding box of non-padded region in
    # model_input_image_shape.
    left, top, right, bottom = get_crop_region(
        model_input_image_shape, original_resolution)
    if not (left <= center[0] <= right and top <= center[1] <= bottom):
        logging.error('Falling back on middle of the image as center')
        return (original_resolution[1]//2, original_resolution[0]//2)
    scale = original_resolution[0] / (bottom - top)

    return (int((center[0] - left) * scale), int((center[1] - top) * scale))


def to_integer(im_np):
    """Converts the image numpy array to integers.

    Args:
        im_np: Image as a numpy array. Either with (some) float dtype and
            value-range [0.0 ... 1.0] or (some) int dtype with value-range
            [0 .... 255].

    Returns:
        Image as a numpy array with integer dtype with value-range [0 ... 255].
    """
    if not np.issubdtype(im_np.dtype, np.integer):
        return (255 * im_np).astype(np.uint8)
    return im_np


def main(argv_for_encoder):
    """Encode images using the attention center.

    First we load the TFLite model. Then for each image in the image directory,
    we use the model to find the center and then encode it using the center.

    Args:
        argv_for_encoder: contains arguments not used by absl flags. Only used
            for those arguments that are passed to the encoder.
    """
    # ignoring the first element here, which is the name of the python script.
    additional_encoder_flags = argv_for_encoder[1:]
    image_dir = pathlib.Path(_IMAGE_DIR.value)
    lite_model_file = _LITE_MODEL_FILE.value
    model_input_image_shape = _MODEL_IMAGE_SHAPE
    output_dir = pathlib.Path(_OUTPUT_DIR.value)
    output_dir.mkdir(parents=True,  exist_ok=True)
    encoder = pathlib.Path(_ENCODER.value)

    # check if the binary for encoding exists
    if not _DRY_RUN:
        if not encoder.exists:
            logging.error(
                f'Can\'t find binary for encoding: {str(encoder)}. Consider'
                'building djxl_ng by following the instructions in'
                './libjxl/README.md or point to an encoder binary with'
                'the \'--encoder\' flag')

    # load the tflite model
    interpreter = load_tflite_model(lite_model_file)

    for filename in sorted(image_dir.iterdir()):
        image_file = image_dir.joinpath(filename)

        im = read_one_image(image_file)
        image_tensor = tf.constant(np.expand_dims(im, axis=0),
                                   dtype=tf.float32)
        resized_image_tensor = tf.image.resize_with_pad(
            image_tensor, model_input_image_shape[0],
            model_input_image_shape[1], method='bicubic', antialias=True)

        # run prediction with tflite
        pred_from_tflite = tflite_predictions(
            interpreter, resized_image_tensor)[0]
        predicted_center = convert_center_to_original_resolution(
            pred_from_tflite, model_input_image_shape,
            (im.shape[0], im.shape[1]))

        center_flags = [str(arg) for pair in zip(
            ('-center_x', '-center_y'), predicted_center) for arg in pair]

        encoded_image = output_dir.joinpath(
            f'{filename.name}.{_NEW_SUFFIX.value}')

        encoder_command = [encoder, *center_flags,
                           *additional_encoder_flags,
                           image_file, encoded_image]

        if _VERBOSE.value or True:
            print(' '.join(map(str, encoder_command)))

        if not _DRY_RUN.value:
            subprocess.run(encoder_command)


if __name__ == '__main__':
    app.run(main)
