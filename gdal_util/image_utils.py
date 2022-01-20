import os
import tempfile

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

    dataset = gdal.Open(filepath)
    response = []
    for band in bands:
        raster = dataset.GetRasterBand(band)
        response.append(raster.ReadAsArray())
    return response[0] if len(response) == 1 else response


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
