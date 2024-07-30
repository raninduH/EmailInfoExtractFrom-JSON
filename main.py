# main file that app starts with

# This has to be outside because of the way the app is structured
# Otherwise the relative imports within api/ and other modules won't work
# This is because the app is started from the root directory and python path is set to the root directory
# so all the imports can be called relative to the root directory
import asyncio
import threading
import time
import uvicorn  # debugging

from fastapi import FastAPI
from email_filtering_and_info_generation.check_notifications import check_notifications_for_managers

from email_authorization.routes import router as authorization_router
from email_filtering_and_info_generation.read_emails import repeat_every_10mins
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


EMAIL_PREFIX = "/email"

# app.include_router(conversation_router, prefix=EMAIL_PREFIX)
# app.include_router(settings_router, prefix=EMAIL_PREFIX)
# app.include_router(filtering_router, prefix=EMAIL_PREFIX)
app.include_router(authorization_router, prefix=EMAIL_PREFIX)
# app.include_router(dashboard_router,prefix=EMAIL_PREFIX)
# app.include_router(suggestions_router,prefix=EMAIL_PREFIX)


def retrieving_emails_loop():
    asyncio.run(repeat_every_10mins())


@app.on_event("startup")
async def on_startup():
    
    # start the continous loop to extract emails in a new thread
    threading.Thread(target=retrieving_emails_loop, args=(), daemon=True).start()




@app.get('/', response_class=RedirectResponse, include_in_schema=False)
async def docs():
    return RedirectResponse(url='/docs')

if __name__ == "__main__":  # debugging
    uvicorn.run(app, host="127.0.0.1", port=8000)