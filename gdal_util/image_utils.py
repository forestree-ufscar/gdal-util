from osgeo import gdal


def get_info(filepath, band=1):
    dataset = gdal.Open(filepath)
    band = dataset.GetRasterBand(band)
    band.DeleteNoDataValue()
    stats = band.GetStatistics(True, True)
    geo_transform = dataset.GetGeoTransform()
    return ImageInfo(stats[0], stats[1], stats[2], stats[3], dataset.RasterXSize, dataset.RasterYSize,
                     dataset.RasterCount, geo_transform[0], geo_transform[1], geo_transform[3], geo_transform[5])


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
