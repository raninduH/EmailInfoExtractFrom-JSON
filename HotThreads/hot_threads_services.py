from datetime import datetime, timedelta
from email_filtering_and_info_generation.configurations.database import collection_conversations

cursor = collection_conversations.find({}, {'thread_id': 1, 'updated_times': 1})

thread_recent_replies_arr = []

for doc in cursor:
    thread_id = doc['thread_id']
    updated_times = doc['updated_times']
    
    now = datetime.utcnow()
    four_days_ago = now - timedelta(days=4)

    # Filter datetime objects within the last 4 days
    filtered_date_times = [dt for dt in updated_times if dt >= four_days_ago]

    # Count the number of datetime objects within the last 4 days
    count_within_last_4_days = len(filtered_date_times)
    
    thread_recent_replies_arr.append({thread_id:count_within_last_4_days})
    
    
    
    

sorted_thread_recent_replies_arr = sorted(thread_recent_replies_arr, key=lambda x: list(x.values())[0], reverse=True)