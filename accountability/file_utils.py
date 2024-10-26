import os
import difflib

def file_exists(file_path):
    if os.path.exists(file_path):
        return True
    return False

def save_if_not_exists(save_directory, file_name, content):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    file_path = os.path.join(save_directory, f"{file_name}.txt")

    if not file_exists(file_path):
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Saved to {file_path}")
    else:
        print(f"Skipping saving {file_path} because it already exists")

    return file_path


def make_filename(date, name):
    return f"{date}-{name}"


def make_bill_directory(base, congress, bill_id):
    return f"{base}/{congress}-{bill_id.replace('/', '-')}"


def get_previous_version_file(file_path, ending_matcher):
    save_directory = os.path.split(file_path)[0]
    file_name = os.path.split(file_path)[1]
    previous_versions = [file for file in os.listdir(save_directory) if file.endswith(ending_matcher) and file != file_name]
    if len(previous_versions) > 0:
        # Get the version before this one.
        # Datetime can be assumed to be in the filename before the ending matcher
        previous_versions.sort(reverse=True)
        previous_version_file_path = os.path.join(save_directory, previous_versions[0])
        print(f"Found previous version: {previous_version_file_path}")
        return previous_version_file_path

    return None


def get_diff(after, before):
    with open(after, 'r') as f1, open(before, 'r') as f2:
        diff = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile=after, tofile=before)
        return ''.join(diff)
