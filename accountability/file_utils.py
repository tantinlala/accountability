import os

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
