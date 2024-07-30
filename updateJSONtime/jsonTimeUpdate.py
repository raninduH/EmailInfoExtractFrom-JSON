import json
from datetime import datetime, timedelta
import logging

file_path = "a0_1_chunks\chunk_10.json"

# Configure logging
logging.basicConfig(level=logging.INFO)

def parse_datetime(datetime_str):
    formats_to_try = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats_to_try:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    logging.error(f"Unexpected datetime format: {datetime_str}")
    return None

try:
    # Parse the JSON data
    with open(file_path, 'r') as file:
        data = json.load(file)

    new_date = 13
    new_year = 2024
    new_month = 6

    # Update the time field in each document
    for doc in data:
        if 'timestamp' in doc:
            current_time = parse_datetime(doc['timestamp'])
            if current_time:
                updated_time = current_time.replace(year=new_year, month=new_month, day=new_date)
                doc['timestamp'] = updated_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                # Handle case where datetime could not be parsed
                # You can decide here how to handle or log these cases
                logging.warning(f"Error parsing datetime: {doc['timestamp']}")
        else:
            logging.warning("Document does not contain 'timestamp' field")

    # Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)
    
    print(f"Successfully updated timestamps in {file_path}")

except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
except Exception as e:
    print(f"Error: {e}")
