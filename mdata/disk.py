import csv
import json


def write_lines_to_file(lines,file_path, mode, delimiter='\n'):
    with open(file_path,mode=mode) as f:
        write_text = delimiter.join(lines) + delimiter
        f.writelines(write_text)


def write_image_to_file(byte_image, file_path):
    with open(file_path, mode='wb') as f:
        f.write(byte_image)


def write_csv(filename, data):
    with open(filename, 'w',newline='') as csvfile:
        exwriter = csv.writer(csvfile,delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        exwriter.writerows(data)


def read_file_to_list(file_path, delimiter='\n'):
    content = read_file(file_path,'r')
    return content.split(delimiter)


def read_file(file_path,mode):
    with open(file_path,mode=mode) as f:
        content = f.read()
    return content


def read_json_configure(config_path):
    with open(config_path) as config_file:
        config = json.load(config_file)
    return config


def read_csv(filename):
    data = []
    with open(filename) as csvfile:
        exreader = csv.reader(csvfile)
        for row in exreader:
            data.append(row)
    return data
