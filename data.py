import os
import datetime
from dotenv import load_dotenv

# Load environmental variables from the ".env" file:
load_dotenv()

# Define constants to be used for e-mailing messages submitted via the "Contact Us" web page:
SENDER_EMAIL_GMAIL = os.getenv("SENDER_EMAIL_GMAIL")
SENDER_PASSWORD_GMAIL = os.getenv("SENDER_PASSWORD_GMAIL") # App password (for the app "Python e-mail", NOT the normal password for the account).
SENDER_HOST = os.getenv("SENDER_HOST")
SENDER_PORT = str(os.getenv("SENDER_PORT"))

# Initialize global variable to be used for displaying website template-design recognition:
recognition_web_template = f"Website template created by the Bootstrap team · © {datetime.datetime.now().year}"

# Define variable to represent the Flask application object to be used for this website:
app = None

# Define variable to represent the database supporting this website:
db = None

# Initialize class variables for database tables:
Cafes = None

# Initialize class variables for web forms:
AddOrEditCafeForm = None
ContactForm = None
