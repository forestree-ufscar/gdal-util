def read_mtl_file(filepath):
    mtl_content = {}
    current_dict_reference = mtl_content
    previous_dict_reference = mtl_content
    with open(filepath) as f:
        for line in f.readlines():
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
