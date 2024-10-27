import os
import difflib

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


def make_filename(date, name):
    return f"{date}-{name}"


def make_bill_directory(base, congress, bill_id):
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
    # Get the part of the filename that is not part of the datetime
    # There should be 2 dashes in the datetime string
    file_name = os.path.basename(filepath)
    dash_splits = file_name.split("-")
    ending_matcher = "-".join(dash_splits[3:])
    save_directory = os.path.dirname(filepath)

    file_name = os.path.split(filepath)[1]
    previous_versions = [file for file in os.listdir(save_directory) if file.endswith(ending_matcher) and file != file_name]
    if len(previous_versions) > 0:
        # Get the version before this one.
        # Datetime can be assumed to be in the filename before the ending matcher
        previous_versions.sort(reverse=True)
        previous_version_filepath = os.path.join(save_directory, previous_versions[0])
        print(f"Found previous version: {previous_version_filepath}")
        return previous_version_filepath

    return None


def get_diff(after, before):
    with open(after, 'r') as f1, open(before, 'r') as f2:
        diff = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile=after, tofile=before)
        return ''.join(diff)
