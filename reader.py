def get_lines_array(path_to_file: str):
    result = []
    with open(path_to_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            name, link = line.split("|:|")
            result.append((name, link))
    return result
