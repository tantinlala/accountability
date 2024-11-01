import os
import difflib
import datetime

def file_exists(filepath):
    if os.path.exists(filepath):
        return True
    return False

def save_if_not_exists(save_directory, file_name, content):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    filepath = os.path.join(save_directory, f"{file_name}.txt")

    if not file_exists(filepath):
        with open(filepath, 'w') as file:
            file.write(content)
        print(f"Saved to {filepath}")
    else:
        print(f"Skipping saving {filepath} because it already exists")

    return filepath


def make_filename(datetime, name):
    return f"{datetime}-{name}"


def get_datetime_and_name_in_filename(filename):
    dash_splits = filename.split("-")
    datetime_string = "-".join(dash_splits[:3])
    datetime_obj = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%SZ")
    name = "-".join(dash_splits[3:])
    return (datetime_obj, name)


def make_bill_path_string(base, congress, bill_id):
    return f"{base}/{congress}-{bill_id.replace('/', '-')}"


def make_summary_filepath(filepath):
    """
    Get base filename without extension
    :param filename: Filename to get base filename from
    :return: Base filename without extension
    """
    save_directory = os.path.dirname(filepath)
    base_filename = os.path.split(filepath)
    base_filename = os.path.splitext(base_filename[1])

    if save_directory[-1] != '/':
        save_directory = save_directory + '/'
    summary_filepath = save_directory + base_filename[0] + '-summary.md'

    return summary_filepath


def get_previous_version_file(filepath):
    file_name = os.path.basename(filepath)
    (datetime_obj, ending_matcher) = get_datetime_and_name_in_filename(file_name)
    file_directory = os.path.dirname(filepath)

    previous_version = None
    for file in os.listdir(file_directory):
        if file == file_name:
            continue

        if not file.endswith(ending_matcher):
            continue

        (older_datetime_obj, unused) = get_datetime_and_name_in_filename(file)

        if older_datetime_obj >= datetime_obj:
            continue

        if previous_version is None or older_datetime_obj > previous_version['datetime']:
            previous_version = {'datetime': older_datetime_obj, 'file': file}
        
    if previous_version:
        return os.path.join(file_directory, previous_version['file'])

    return None


def get_diff(after, before):
    with open(after, 'r') as f1, open(before, 'r') as f2:
        diff = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile=after, tofile=before)
        return ''.join(diff)
