import copy
import os
import asyncio
import json
import re

from simplegmail import Gmail # type: ignore
from simplegmail.query import construct_query # type: ignore
from datetime import datetime, timedelta, timezone
from email_filtering_and_info_generation.conversations_summarizing import summarize_conversations
from email_filtering_and_info_generation.emailIntegration import integrateEmail
from email_filtering_and_info_generation.criticality_identification import identify_criticality
from email_filtering_and_info_generation.format_email_bodies import format_email_bodies
from email_filtering_and_info_generation.issues_identification import identify_issues_inquiries_and_checking_status
from email_filtering_and_info_generation.notificationidentification import identify_notifcations
from email_filtering_and_info_generation.data_masking import mask_email_messages
from email_filtering_and_info_generation.sentiment_analysis import identify_sentiments
from email_filtering_and_info_generation.topic_identification import identify_topics
from email_filtering_and_info_generation.suggestions_identification import identify_and_summarize_suggestions


from email_authorization.services import refresh_token, is_token_valid, login_async

from email_filtering_and_info_generation.services import get_all_reading_accounts
from email_authorization.services import  update_authorization_uri
from email_filtering_and_info_generation.services import send_email_message,get_reading_emails_array

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow # type: ignore
from pathlib import Path

from googleapiclient.discovery import build 
from google.oauth2.credentials import Credentials
import os.path 
import base64 
from bs4 import BeautifulSoup 

import threading
import requests
import time
from dateutil.parser import isoparse


# email accounts array
email_acc_array = []

state_store = {}

last_email_read_time = ""


# input the email_acc_array and then return the updated email_acc_array
# email_acc_array=integrateEmail()




async def getEmails(id: int, new_email_msg_array, email_acc_address:str, last_email_read_time): 
    # Variable creds will store the user access token. 
    # If no valid token found, we will create one. 
    
    token_path = f'api/email_filtering_and_info_generation/credentialsForEmails/credentialsForEmail{id}/gmail_token.json'
    
    if (os.path.exists(token_path)):
        refresh_token(token_path)
    
    if not is_token_valid(token_path):
        
        await login_async(id, email_acc_address)
        
    
    while(not os.path.exists(token_path)):
        print("inside waiting loop")
        time.sleep(5)
    
    print("outside of waiting loop")
    creds = None
    
    SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.settings.basic'
    ]
    
    
    
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)


    # Connect to the Gmail API 
    service = build('gmail', 'v1', credentials=creds) 
    
    if last_email_read_time == "":
        # Calculate the timestamp for 10 minutes ago
        ten_minutes_ago = datetime.utcnow() - timedelta(minutes=600)
        ten_minutes_ago_unix = int(ten_minutes_ago.timestamp())
        
        # Request a list of all the messages received after the calculated timestamp
        result = service.users().messages().list(userId='me', q=f'after:{ten_minutes_ago_unix}').execute()        
        
    else:
        
        start_datetime_str = last_email_read_time
        start_datetime = datetime.strptime(start_datetime_str, "%a, %d %b %Y %H:%M:%S %z")

        # Convert the start_datetime to Unix timestamp
        start_timestamp = int(start_datetime.timestamp())
        
        # Request a list of all the messages received after the specified datetime
        result = service.users().messages().list(userId='me', q=f'after:{start_timestamp}').execute()
        
        
        
    messages = result.get('messages', []) 
    
   
    
    # messages is a list of dictionaries where each dictionary contains a message id
    # iterate through all the messages 
    for msg in messages: 
        # Get the message from its id 
        txt = service.users().messages().get(userId='me', id=msg['id']).execute() 
  
        # Use try-except to avoid any Errors 
        try: 
            # Get value of 'payload' from dictionary 'txt' 
            payload = txt['payload'] 
            headers = payload['headers'] 
            # Extract metadata
            metadata = {}
  
            # Look for Subject and Sender Email in the headers 
            # Iterate through headers to find relevant metadata
            for header in headers:
                if header['name'] == 'Date':
                    metadata['Received Time'] = header['value']
                    
                    # update the the last email read time, bcz the first email of the list is the latest one.
                    if messages[0]['id']==msg['id']:
                        last_email_read_time =  metadata['Received Time']
                        
                elif header['name'] == 'To':
                    metadata['Recipient'] = header['value']
                elif header['name'] == 'From':
                    metadata['Sender'] = header['value']
                elif header['name'] == 'Subject': 
                    subject = header['value']
                    
            # Extract email ID and thread ID
            metadata['Email ID'] = msg['id']
            metadata['Thread ID'] = msg['threadId']
            # The Body of the message is in Encrypted format. So, we have to decode it. 
            # Get the data and decode it with base 64 decoder. 
            parts = payload.get('parts')[0] 
            data = parts['body']['data'] 
            data = data.replace("-","+").replace("_","/") 
            decoded_data = base64.b64decode(data) 
  
            # Now, the data obtained is in lxml. So, we will parse  
            # it with BeautifulSoup library 
            soup = BeautifulSoup(decoded_data , "lxml") 
            # body = soup.body() 
            # body = soup.get_text()
            
            # Extract the text without HTML tags and Liquid markup
            body = re.sub(r'{%.*?%}', '', soup.get_text())  # Remove Liquid markup
            # Remove extra white spaces
            body = re.sub(r'\s+', ' ', body).strip()
            
            # Printing the subject, sender's email and message 
            #print("Subject: ", subject)       
            # print("Recipient:", metadata.get('Recipient'))
            # print("Sender:", metadata.get('Sender'))
            # print("Email ID:", metadata.get('Email ID'))
            # print("Thread ID:", metadata.get('Thread ID'))
            # print("Received Time:", metadata.get('Received Time'))
            #print("MESSAGE BODY: ", body) 
            # print('\n') 
            # print('\n') 
            
            email_msg_dict = {"id": metadata.get('Email ID'),"time":metadata.get('Received Time'), "recipient": metadata.get('Recipient'), "sender": metadata.get('Sender'), "subject": subject,
                            "thread_id": metadata.get('Thread ID'), "body":body, "criticality_category":"", "our_sentiment_score":0, "products":[], "isSuggestion":False, "isIssue":False, "isInquiry":False}

            print("email_msg_dict", email_msg_dict)
            # append the new email msg dict to the new_email_msg_array
            print("appending a msg to the new email msg array")
            new_email_msg_array.append(email_msg_dict)
            
            print("new email msg array after appending", new_email_msg_array)
        except: 
            pass




async def read_all_new_emails(new_email_msg_array):
    
    # email_acc_array = await get_reading_emails_array()
    file_path = r"a0_9_chunks\chunk_2.json"
    
    print("Now doing : ", file_path)
 
    with open(file_path, 'r') as file:
        documents = json.load(file)
        for message in documents:
            
                # Input string in format "2024-06-17T15:12:54Z"
                input_string = message["timestamp"]

                # Step 1: Parse the input string into a datetime object
                dt = datetime.strptime(input_string, "%Y-%m-%dT%H:%M:%SZ")

                # Step 2: Ensure the datetime object is in UTC
                dt = dt.replace(tzinfo=timezone.utc)
            
                email_msg_dict={"time":dt, "recipient": message["receiver"], "sender": message["sender"], "subject": message["subject"],"type":"",
                    "thread_id": message["thread_id"], "body":message["message_body"], "criticality_category":"", "org_sentiment_score":0, "our_sentiment_score":0, "products":[], "isSuggestion":False, "isIssue":False, "isInquiry":False}

                 # append the new email msg dict to the new_email_msg_array
                print("appending a msg to the new email msg array")
                new_email_msg_array.append(email_msg_dict)

        
        
    print("\n")
    print("\n")
    print("\n")
    print("\n")  
    #print("new email msg array after appending ALL", new_email_msg_array)   

    
    
async def push_new_emails_to_DB(new_email_msg_array):
    
    temp_email_msg_array = copy.deepcopy(new_email_msg_array)
    for temp_email_msg in temp_email_msg_array:
        del temp_email_msg["body"]
        await send_email_message(temp_email_msg)
    
async def repeat_every_10mins():

    
    # Continuously run the task every 'interval' seconds. 600 = 10 minutes.
    # this is currently set to 1 minute. change it later.
    print("it's happening")
    print("read_all_new_emails happening")
    new_email_msg_array = []
    last_email_read_time = ""
    await read_all_new_emails(new_email_msg_array)
    print("\n")
    print("\n")
    #print("RAW READ NEW EMAIL MESG ARRAY", new_email_msg_array)
    await mask_email_messages(new_email_msg_array)
    #print("MASKED EMAIL MESSAGES", new_email_msg_array)
    # await format_email_bodies(new_email_msg_array)
    print("\n")
    print("\n formatted email bodies")
    print("\n")
    #print("formatted EMAIL BODIES----------",new_email_msg_array)
    identify_sentiments(new_email_msg_array)
    await identify_criticality(new_email_msg_array)
    time.sleep(3)
    print("\n")
    print("\n criticality identified emails")
    print("\n")
    #print(new_email_msg_array)
    # await identify_notifcations(new_email_msg_array)
    await identify_topics(new_email_msg_array)
    print("\n")
    print("\n Products identified emails")
    print("\n")
    #print("emails with topics",new_email_msg_array)
    await identify_issues_inquiries_and_checking_status(new_email_msg_array) # make sure to perform this before the coversations_summarizing
    # print("---------------------------------------finished identify issues------------------------------")
    #time.sleep(10)
    print("\n")
    print("\n Issues and Inquiries identified emails")
    print("\n")
    #print(new_email_msg_array)
    await identify_and_summarize_suggestions(new_email_msg_array)
    print("\n")
    print("\n Suggestions identified emails")
    print("\n")
    #print(new_email_msg_array)
    # print("---------------------------------------finished identifying summaries------------------------")

    await push_new_emails_to_DB(new_email_msg_array)
    print("database update successful")
    await summarize_conversations(new_email_msg_array)
    print("conversation summaries identified")
    
    # make this 10 minutes
    interval = 7000
    next_time = time.time() + interval
    while True:
        time.sleep(max(0, next_time - time.time()))
        try:
            new_email_msg_array = []
            last_email_read_time = ""
            await read_all_new_emails(new_email_msg_array)
            print("\n")
            print("\n")
            print("RAW READ NEW EMAIL MESG ARRAY", new_email_msg_array)
            await mask_email_messages(new_email_msg_array)
            print("MASKED EMAIL MESSAGES", new_email_msg_array)
            await format_email_bodies(new_email_msg_array)
            print("\n")
            print("\n formatted email bodies")
            print("\n")
            print("formatted EMAIL BODIES----------",new_email_msg_array)
            identify_sentiments(new_email_msg_array)
            identify_criticality(new_email_msg_array)
            print("\n")
            print("\n criticality identified emails")
            print("\n")
            print(new_email_msg_array)
            await identify_notifcations(new_email_msg_array)
            # await identify_topics(new_email_msg_array)
            print("\n")
            print("\n Products identified emails")
            print("\n")
            print("emails with topics",new_email_msg_array)
            # # print(new_email_msg_array)
            # #print(new_email_msg_array)
            await identify_issues_inquiries_and_checking_status(new_email_msg_array) # make sure to perform this before the coversations_summarizing
            # print("---------------------------------------finished identify issues------------------------------")
            print("\n")
            print("\n Issues and Inquiries identified emails")
            print("\n")
            print(new_email_msg_array)
            await identify_and_summarize_suggestions(new_email_msg_array)
            print("\n")
            print("\n Suggestions identified emails")
            print("\n")
            print(new_email_msg_array)
            # print("---------------------------------------finished identifying summaries------------------------")
            # print(new_email_msg_array)
            await push_new_emails_to_DB(new_email_msg_array)
            print("database update successful")
            await summarize_conversations(new_email_msg_array)
            print("conversation summaries identified")
                    
        except Exception as e:
            print("Error:", e)
        # Calculate the next execution time
        next_time += (time.time() - next_time) // interval * interval + interval















































#
#         with open("email_samples.txt", "a") as f:
#             if message.plain:
#                 if len(message.plain)<1000:
#                     f.write(message.plain)
#
#
