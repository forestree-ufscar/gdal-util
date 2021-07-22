def get_mtl_filename_from_band_file(filename):
    filename = filename.split(".")[0]
    return filename.split("_")[0] + "_MTL.txt"


def read_mtl_from_content(content: str):
    return _read_mtl_from_content(content.splitlines())


def read_mtl_file(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    return _read_mtl_from_content(lines)


def _read_mtl_from_content(content):
    mtl_content = {}
    current_dict_reference = mtl_content
    previous_dict_reference = mtl_content
    for line in content:
        stripped_line = line.strip()
        if stripped_line.startswith("GROUP"):
            previous_dict_reference = current_dict_reference
            current_dict_reference[stripped_line[8:]] = {}
            current_dict_reference = current_dict_reference[stripped_line[8:]]
        elif stripped_line.startswith("END"):
            current_dict_reference = previous_dict_reference
        else:
            key_value_pair = stripped_line.split(" = ")
            current_dict_reference[key_value_pair[0]] = key_value_pair[1].replace("\"", "")
    return mtl_content


def get_band_name_from_mtl_file(band, filename):
    mtl_content = read_mtl_file(filename)
    return get_band_name_from_mtl_content(band, mtl_content)


def get_band_name_from_mtl_content(band, mtl_content):
    return mtl_content["L1_METADATA_FILE"]["PRODUCT_METADATA"][f"FILE_NAME_BAND_{band}"].replace("LC", "LO")


def get_inpe_name_from_mtl_file(filename):
    mtl_content = read_mtl_file(filename)
    return get_inpe_name_from_mtl_content(mtl_content)


def get_inpe_name_from_mtl_content(mtl_content):
    orbit = mtl_content["L1_METADATA_FILE"]["PRODUCT_METADATA"]["WRS_PATH"]
    point = mtl_content["L1_METADATA_FILE"]["PRODUCT_METADATA"]["WRS_ROW"]
    date = mtl_content["L1_METADATA_FILE"]["PRODUCT_METADATA"]["DATE_ACQUIRED"]
    return f"L8-OLI {int(orbit):03d}/{int(point):03d} {date}"
