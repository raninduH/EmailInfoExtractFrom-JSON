
import time
from email_filtering_and_info_generation.models import Convo_summary
from langchain_google_genai import ChatGoogleGenerativeAI
from email_filtering_and_info_generation.services import send_convo_summary, update_summary
 
import google.generativeai as genai
import os
from dotenv import load_dotenv

from email_filtering_and_info_generation.configurations.database import collection_conversations



# Load environment variables from .env file
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
google_api_key_2 = os.getenv("GOOGLE_API_KEY_2")
google_api_key_3 = os.getenv("GOOGLE_API_KEY_3")

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7,api_key=google_api_key)


async def summarize_conversations(new_email_msg_array):
    
    i = 0
    # Query to get all thread_ids
    
    
    
    new_convo_summaries_array = []
    
    email_no = 1
    
    for new_email_msg in new_email_msg_array:
        
        if(i%3==0):
            llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7,api_key=google_api_key)
        elif(i%3==1): 
            llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7,api_key=google_api_key_2)
        else:   
            llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7,api_key=google_api_key_3)
            
            
        i = i+1
        
        try:
        
            document = collection_conversations.find_one({'thread_id': new_email_msg["thread_id"]})
            
            print("\n email_no:", email_no, " \n thread_id", new_email_msg["thread_id"])
            email_no = email_no + 1
            full_convo_text = ""
            
            if document:
                
                convo_summary_doc = document
                prev_summary = convo_summary_doc['summary']
                
                full_convo_text = new_email_msg["body"] + " " + prev_summary
                
                #print("current updated times", convo_summary_doc['updated_times'], "thread_id", new_email_msg["thread_id"])
                convo_summary_doc['updated_times'].append(new_email_msg["time"])
                new_updated_times = convo_summary_doc['updated_times'] 
                
            else:
                
                full_convo_text = new_email_msg["body"]
            
        
            
            
            conversation_summarizing_script = f"""Write a summary of this text '{full_convo_text}'. The summary should summarize what the above email conversation is about and 
            it shoudl be able to give the reader an undersating about the email conversation in a very short time. Also, only output the summary. 
            Don't output anything else.These emails are either ones that came to a customer care email account of a company, or the emails sent by that company to their customers, so provide the summary as you are summarzing these to a company manager. """
            
            # Send the full convo text to Gemini for summarizing
            response = llm.invoke(conversation_summarizing_script)  
            

            
            # at last adding the new_email_id to the array
            
            if document:
                print("ongoing summary")
                print("\n")
                print("summary")
                print(response.content)   
                print("\n") 
                
                await update_summary(new_email_msg["thread_id"], response.content, new_updated_times)
            
            else:
                print("new summary")
                print("\n")
                print("summary")
                print(response.content)   
                print("\n") 
                            
                if(new_email_msg["time"]==None):
                    print("time is None email arrived!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    time.sleep(5)
                
                new_convo_summary = Convo_summary(
                                    thread_id=new_email_msg["thread_id"], 
                                    subject = new_email_msg["subject"], 
                                    updated_times= [new_email_msg["time"]], 
                                    summary=response.content,
                                    products=new_email_msg["products"])
                
                await send_convo_summary(new_convo_summary)
                
                
        except Exception as e:
            
            print("Exception : ", e)
            print("oooooooooooooooooooooooooooooooooooooooooooooooooooooo  Summary identiifcation skipped in the ", email_no-1, " email  ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo")
            
        
        
        
        
        
        