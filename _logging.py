import os
import logfire
from dotenv import load_dotenv

load_dotenv()

logfire.configure(token=os.environ.get("LOGFIRE_TOKEN"))
logfire.instrument_pydantic_ai()
