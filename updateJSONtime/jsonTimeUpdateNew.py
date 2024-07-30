import json
from datetime import datetime

# Define the new month and day you want to set
NEW_MONTH = 6  # July
NEW_DAY = 10

def update_timestamp(timestamp_str, new_month, new_day):
    # Parse the original timestamp
    original_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
    # Create a new timestamp with the updated month and day
    updated_timestamp = original_timestamp.replace(month=new_month, day=new_day)
    # Format the updated timestamp back to the original format
    return updated_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

def update_json_file(file_path, new_month, new_day):
    # Read the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Update the timestamp in each document
    for doc in data:
        if 'timestamp' in doc:
            doc['timestamp'] = update_timestamp(doc['timestamp'], new_month, new_day)

    # Write the updated data back to the same JSON file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Define the file path
file_path = 'a0_1_chunks\chunk_1.json'

# Update the JSON file
update_json_file(file_path, NEW_MONTH, NEW_DAY)

print(f"Updated JSON data has been written to {file_path} DAY {NEW_DAY}")
