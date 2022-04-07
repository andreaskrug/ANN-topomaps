"""
Functions for computing topographic map quality
"""

import numpy as np
import os
from matplotlib import pyplot as plt
from PIL import ImageFilter
from sklearn.metrics import auc
from pdf2image import convert_from_path


def topomap_rescale(img, shrink_size):
    """
    downscaling an image and upscaling it
    :param img: input PIL image
    :param shrink_size: shrink size coefficient
    :return: processed image as ndarray
    """
    shrink_size = 55 - (shrink_size * 5)
    res_img = img.resize((shrink_size, shrink_size))
    res_img_big = res_img.resize(img.size)
    arr_img_rescaled = np.asarray(res_img_big)
    return arr_img_rescaled


def topomap_blur(img, radius):
    """
    blurring an image
    :param img: input PIL image
    :param radius: blur radius coefficient
    :return: blurred image as ndarray
    """
    radius = (radius * 2) + 2
    blur_img = img.filter(ImageFilter.GaussianBlur(radius))
    arr_img_blurred = np.asarray(blur_img)
    return arr_img_blurred


def topomap_mse(image_path, metric, params, output_dir=None):
    """
    compute Mean Squared Error of an image and altered versions of if
    :param image_path: path to the stored image
    :param metric: image alteration method ['resize_mse', 'blur_mse']
    :param params: list of parameters of the image alteration method
    :param output_dir: output directory, if the changed images shall be stored
    :return: MSEs as ndarray
    """
    img = convert_from_path(image_path)[0]
    arr_img = np.asarray(img)

    if output_dir is not None:
        nrow, ncol = [1, len(params) + 1]
        fig, axes = plt.subplots(nrow, ncol, figsize=(2 * ncol, 2 * 0.95 * nrow))
        axes[0].imshow(arr_img)
        axes[0].set_xticks([])
        axes[0].set_yticks([])

    img_manipulation_fn = None
    if metric == 'resize_mse':
        img_manipulation_fn = topomap_rescale
    elif metric == 'blur_mse':
        img_manipulation_fn = topomap_blur

    errs = np.zeros(len(params))
    for i, param in enumerate(params):
        arr_img_changed = img_manipulation_fn(img, param)
        if output_dir is not None:
            axes[i + 1].imshow(arr_img_changed)
            axes[i + 1].set_xticks([])
            axes[i + 1].set_yticks([])

        err = np.square(arr_img - arr_img_changed).mean()
        errs[i] = err

    if output_dir is not None:
        fig.savefig(os.path.join(output_dir, image_path.split("/")[-1][:-4] + "_" + metric + '.pdf'),
                    format='pdf', bbox_inches='tight', pad_inches=0.02)
        plt.close(fig)

    img.close()
    return errs


def compute_topomap_image_quality(image_dir, metric, params, return_auc=False, output_dir=None):
    """
    compute quality of topographic maps for multiple groups
    :param image_dir: path to directory with the stored topographic map images
    :param metric: image alteration method ['resize_mse', 'blur_mse']
    :param params: list of parameters of the image alteration method
    :param return_auc: whether to compute an estimated Area Under the Curve value
    :param output_dir: output directory, if the changed images shall be stored
    :return: quality values as ndarray
    """


    image_paths = os.listdir(image_dir)

    group_errors = []
    for image_path in image_paths:
        group_errors.append(topomap_mse(os.path.join(image_dir, image_path),
                                        metric,
                                        params,
                                        output_dir=output_dir))
    group_errors = np.array(group_errors)
    quality_values = list(np.mean(group_errors, axis=0))

    if return_auc:
        mse_auc = auc(np.arange(len(quality_values)), quality_values)
        quality_values.append(mse_auc)

    return np.array(quality_values)
