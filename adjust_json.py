import json
import os

# Define the path to your JSON file
# input_file = '\\instant-ngp\\data\\nerf\\portal_gun\\transforms.json'
# output_file = '\\instant-ngp\\data\\nerf\\portal_gun\\transforms.json'

input_file = 'transforms.json'
output_file = input_file

# Function to modify file paths
def modify_file_paths(data):
    for frame in data.get('frames', []):
        file_path = frame.get('file_path', '')
        # Extract the file name part (e.g., r_67.png) from the file path
        base_name = os.path.basename(file_path)
        # Update the file path format
        frame['file_path'] = f"images/{base_name}"
    return data

# Read the JSON file
with open(input_file, 'r') as file:
    json_data = json.load(file)

# Modify the file paths
modified_data = modify_file_paths(json_data)

# Write the updated JSON data to a new file
with open(output_file, 'w') as file:
    json.dump(modified_data, file, indent=4)

print(f"Updated JSON has been saved to {output_file}")
