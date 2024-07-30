import json
from datetime import datetime, timedelta
import logging
import random

file_path = "a0_9_chunks/chunk_1.json"

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

    new_date = 11
    new_year = 2024
    new_month = 7

    # Initialize the starting time at 8:00 AM
    previous_time = datetime(new_year, new_month, new_date, 8, 0)

    # Update the time field in each document
    for doc in data:
        if 'timestamp' in doc:
            # Ensure current_time is parsed successfully
            current_time = parse_datetime(doc['timestamp'])
            if current_time:
                # Set the initial timestamp for the first document
                if data.index(doc) == 0:
                    updated_time = previous_time
                else:
                    # Randomly add between 1 to 59 minutes to the previous time for subsequent documents
                    random_minutes = random.randint(1, 59)
                    updated_time = previous_time + timedelta(minutes=random_minutes)
                    if updated_time.day != new_date:  # Ensure the time stays within the same day
                        updated_time = datetime(new_year, new_month, new_date, 23, 59)
                
                doc['timestamp'] = updated_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                previous_time = updated_time
            else:
                # Handle case where datetime could not be parsed
                logging.warning(f"Error parsing datetime: {doc['timestamp']}")
        else:
            logging.warning("Document does not contain 'timestamp' field")

    # Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)
    
    print(f"Successfully updated timestamps in {file_path} with date {new_date}")

except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
except Exception as e:
    print(f"Error: {e}")
