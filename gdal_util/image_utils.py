import math
import os
import tempfile

import numpy as np
from osgeo import gdal
from osgeo_utils import gdal_merge

ORFEO_TOOLBOX_PATH = os.path.join(os.getenv("ORFEO_TOOLBOX_PATH"), "bin")


def get_info(filepath, band=1):
    dataset = gdal.Open(filepath)
    band = dataset.GetRasterBand(band)
    band.DeleteNoDataValue()
    stats = band.GetStatistics(True, True)
    geo_transform = dataset.GetGeoTransform()
    return ImageInfo(stats[0], stats[1], stats[2], stats[3], dataset.RasterXSize, dataset.RasterYSize,
                     dataset.RasterCount, geo_transform[0], geo_transform[1], geo_transform[3], geo_transform[5])


def read_raster(filepath, bands=None):
    if bands is None:
        bands = [1]
    elif isinstance(bands, int):
        bands = list(range(1, bands))

    dataset = gdal.Open(filepath)
    response = []
    for band in bands:
        raster = dataset.GetRasterBand(band)
        response.append(raster.ReadAsArray())
    return response[0] if len(response) == 1 else np.asarray(response)


def merge_image(output_file, inputs):
    gdal_merge.main(["", "-separate", "-of", "GTiff", "-o", output_file] + inputs)


def superimpose(output_file, input_pan, input_mosaic):
    cmd = os.path.join(ORFEO_TOOLBOX_PATH,
                       "otbcli_Superimpose") + " -lms 0 -interpolator linear -elev.default 0 -inr {} -inm {} -out {}" \
              .format(input_pan, input_mosaic, output_file)
    os.system(cmd)


def pansharpening_command(output_file, input_pan, input_super):
    cmd = os.path.join(ORFEO_TOOLBOX_PATH, "otbcli_Pansharpening") + " -method rcs -inp {} -inxs {} -out {}" \
        .format(input_pan, input_super, output_file)
    os.system(cmd)


def convert_int16(output_file, input_file, no_data=0):
    options = gdal.TranslateOptions(format='GTiff', outputType=gdal.GDT_UInt16, noData=no_data)
    gdal.Translate(output_file, input_file, options=options)


def pansharpening(output_file, merge_files, pan_file, temp_folder=tempfile.gettempdir()):
    merge_output = tempfile.mktemp(suffix=".tif", dir=temp_folder)
    merge_image(merge_output, merge_files)

    superimpose_output = tempfile.mktemp(suffix=".tif", dir=temp_folder)
    superimpose(superimpose_output, pan_file, merge_output)
    os.remove(merge_output)

    pansharpening_output = tempfile.mktemp(suffix=".tif", dir=temp_folder)
    pansharpening_command(pansharpening_output, pan_file, superimpose_output)
    os.remove(superimpose_output)

    convert_int16(output_file, pansharpening_output)
    os.remove(pansharpening_output)


def get_patches(bands, x, y, path, percent=0.7, augmentation=False, all_patches=False):
    """
    inputs:
        bands: number of bands
        x: x size of path
        y: y size of path
        path: image path
        percent: minimum of pixels in a path
    output:
        patch_xy array
    """

    patches = []
    raster_array = read_raster(path, bands)
    shape = raster_array.shape

    for i in range(0, shape[1], x):
        for j in range(0, shape[2], y):
            patch_ij = raster_array[0:bands, i:i + x, j:j + y]
            if patch_ij.mean() > 0 or all_patches:
                patch_xy = np.zeros((bands, x, y))
                patch_xy[0:bands - 1, 0:min(x, shape[1] - i), 0:min(y, shape[2] - j)] = patch_ij

                if all_patches or np.count_nonzero(patch_xy) > x * y * percent * bands:
                    patches.append(patch_xy if not augmentation else _get_augmentation(patch_xy, bands))

    return patches


def _get_augmentation(patch_xy, bands):
    flip = np.flip(patch_xy)
    flip_0 = np.flip(patch_xy, 0)
    flip_1 = np.flip(patch_xy, 1)

    matrix_b = []
    for b in range(0, bands):
        matrix = []

        for width in range(0, min(patch_xy.shape[1], flip.shape[1])):
            matrix.append(np.concatenate((patch_xy[b][width], flip[b][width])))

        for height in range(0, min(flip_0.shape[1], flip_1.shape[1])):
            matrix.append(np.concatenate((flip_0[b][height], flip_1[b][height])))

        matrix_b.append(matrix)

    return np.array(matrix_b)


def reduce_image(input_file, output_file, top_left, down_right, no_data=0, proj_win_srs="EPSG:32722"):
    proj_win = [top_left.x, top_left.y, down_right.x, down_right.y]
    options = gdal.TranslateOptions(format="GTiff", projWin=proj_win, noData=no_data, projWinSRS=proj_win_srs)
    gdal.Translate(output_file, input_file, options=options)


def get_areas_of_fragmented_image(path, x_size, y_size, image_percent=0.8):
    info = get_info(path)
    rc = info.raster_coordinate
    x_res = info.west_east_resolution
    y_res = info.north_south_resolution
    raster = read_raster(path, info.raster_count)
    min_data = x_size * y_size * info.raster_count * image_percent

    data_areas = []
    for x in range(math.ceil(rc.top_left.x), math.floor(rc.down_right.x - (x_res * x_size)), int(x_res * x_size)):
        for y in range(math.ceil(rc.top_left.y), math.floor(rc.down_right.y - (y_res * y_size)), int(y_res * y_size)):
            x_pixel = int((x - math.ceil(rc.top_left.x)) / x_res)
            y_pixel = int((y - math.ceil(rc.top_left.y)) / y_res)

            patch = raster[0:info.raster_count, y_pixel:y_pixel + y_size, x_pixel:x_pixel + x_size]
            if (image_percent < 1 and np.count_nonzero(patch) > min_data) or patch.min() > 0:
                top_left = PixelCoordinate(x, y)
                down_right = PixelCoordinate(x + (x_res * x_size), y + (y_res * y_size))
                data_areas.append((top_left, down_right))

    return data_areas


class ImageInfo:

    def __init__(self, minimum, maximum, mean, std_dev, raster_x_size, raster_y_size, raster_count,
                 top_left_x, west_east_resolution, top_left_y, north_south_resolution):
        self.minimum = minimum
        self.maximum = maximum
        self.mean = mean
        self.std_dev = std_dev
        self.raster_x_size = raster_x_size
        self.raster_y_size = raster_y_size
        self.raster_count = raster_count
        self.west_east_resolution = west_east_resolution
        self.north_south_resolution = north_south_resolution
        self.raster_coordinate = ImageCoordinate(PixelCoordinate(top_left_x, top_left_y),
                                                 PixelCoordinate(top_left_x + raster_x_size * west_east_resolution,
                                                                 top_left_y),
                                                 PixelCoordinate(top_left_x,
                                                                 top_left_y + raster_y_size * north_south_resolution),
                                                 PixelCoordinate(top_left_x + raster_x_size * west_east_resolution,
                                                                 top_left_y + raster_y_size * north_south_resolution))


class ImageCoordinate:

    def __init__(self, top_left, top_right, down_left, down_right):
        self.top_left = top_left
        self.top_right = top_right
        self.down_left = down_left
        self.down_right = down_right


class PixelCoordinate:

    def __init__(self, x, y):
        self.x = x
        self.y = y
