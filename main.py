# PROFESSIONAL PROJECT: Cafe and WiFi Website

# OBJECTIVE: To implement a website offering users a way to add, edit, and view information on cafes and their amenities.

# Import necessary library(ies):
from data import app, db, recognition_web_template,  SENDER_EMAIL_GMAIL, SENDER_HOST, SENDER_PASSWORD_GMAIL, SENDER_PORT
from data import Cafes, AddOrEditCafeForm, ContactForm
from datetime import datetime
from dotenv import load_dotenv
import email_validator
from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
import os
import smtplib
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import traceback
from wtforms.validators import InputRequired, Length, Email, URL
from wtforms import EmailField, StringField, SubmitField, TextAreaField, BooleanField
import wx


# Initialize the Flask app. object:
app = Flask(__name__)

# Create needed class "Base":
class Base(DeclarativeBase):
  pass


# Define variable to be used for showing user dialog and message boxes:
dlg = wx.App()

# NOTE: Additional configurations are launched via the "run_app" function defined below.


# CONFIGURE ROUTES FOR WEB PAGES (LISTED IN HIERARCHICAL ORDER STARTING WITH HOME PAGE, THEN ALPHABETICALLY):
# ***********************************************************************************************************
# Configure route for home page:
@app.route('/')
def home():
    global db, app

    try:
        # Go to the home page:
        return render_template("index.html", recognition_web_template=recognition_web_template)
    except:
        # Log error into system log file:
        update_system_log("route: '/'", traceback.format_exc())

        # Go to the web page which displays error details to the user:
        return render_template("error.html", activity="route: '/'", details=traceback.format_exc())


# Configure route for "About" web page:
@app.route('/about')
def about():
    global db, app

    try:
        # Go to the "About" page:
        return render_template("about.html", recognition_web_template=recognition_web_template)

    except:
        # Log error into system log file:
        update_system_log("route: '/about'", traceback.format_exc())

        # Go to the web page which displays error details to the user:
        return render_template("error.html", activity="route: '/about'", details=traceback.format_exc())


# Configure route for "Edit Cafe" web page:
@app.route('/add_cafe',methods=["GET", "POST"])
def add_cafe():
    global db, app

    try:
        # Instantiate an instance of the "AddOrEditCafeForm" class:
        form = AddOrEditCafeForm()

        if form.validate_on_submit():
            # Initialize variable to summarize end result of this transaction attempt:
            result = ""

            # Initialize variable to track whether cafe name has violated the unique-value constraint:
            unique_cafe_name_violation = False

            # Check if name of new cafe already exists in the db.  Capture feedback to relay to enf user:
            cafe_name_in_db = retrieve_from_database("get_cafe_by_name", cafe_name=form.txt_name.data)
            if cafe_name_in_db == {}:
                result = "An error has occurred. Cafe has not been added."
            elif cafe_name_in_db != None:
                result = f"Cafe name '{form.txt_name.data}' already exists in the database.  Please go back and enter a unique cafe name."
                unique_cafe_name_violation = True
            else:
                # Add the new cafe record from the database.  Capture feedback to relay to end user:
                if not update_database("add_cafe", form=form):
                    result = "An error has occurred. Cafe has not been added."
                else:
                    result = "Cafe has been successfully added."

            # Go to the web page to render the results:
            return render_template("db_update_result.html", unique_cafe_name_violation=unique_cafe_name_violation, trans_type="Add", result=result,
                                   recognition_web_template=recognition_web_template)

        # Go to the "Add Cafe" web page:
        return render_template("add_cafe.html", form=form, recognition_web_template=recognition_web_template)

    except:  # An error has occurred.
        # Log error into system log file:
        update_system_log("route: '/add_cafe'", traceback.format_exc())

        # Go to the web page which displays error details to the user:
        return render_template("error.html", activity="route: '/add_cafe'", details=traceback.format_exc())


# Configure route for "Cafes" web page:
@app.route('/cafes')
def cafes():
    global db, app

    try:
        # Initialize variables to track whether existing cafe records were successfully obtained or if an error has occurred:
        success = False
        error_msg = ""
        cafe_count = 0

        # Get information on existing cafes in the database. Capture feedback to relay to enf user:
        existing_cafes = retrieve_from_database("get_all_cafes")
        if existing_cafes == {}:
            error_msg = "An error has occurred. Cafe information cannot be obtained at this time."
        elif existing_cafes == []:
            error_msg = "No matching records were retrieved."
        else:
            cafe_count = len(existing_cafes)  # Record count to be displayed in the sub-header of the "Cafes" web page.

            # Indicate that record retrieval has been successfully executed:
            success = True

        # Go to the web page to render the results:
        return render_template("cafes.html", cafes=existing_cafes, cafe_count=cafe_count, success=success, error_msg=error_msg, recognition_web_template=recognition_web_template)

    except:  # An error has occurred.
        # Log error into system log file:
        update_system_log("route: '/cafes'", traceback.format_exc())

        # Go to the web page which displays error details to the user:
        return render_template("error.html", activity="route: '/cafes'", details=traceback.format_exc())


# Configure route for "Contact Us" web page:
@app.route('/contact',methods=["GET", "POST"])
def contact():
    global db, app

    try:
        # Instantiate an instance of the "ContactForm" class:
        form = ContactForm()

        # Validate form entries upon submittal. If validated, send message:
        if form.validate_on_submit():
            # Send message via e-mail:
            msg_status = email_from_contact_page(form)

            # Go to the "Contact Us" page and display the results of e-mail execution attempt:
            return render_template("contact.html", msg_status=msg_status, recognition_web_template=recognition_web_template)

        # Go to the "Contact Us" page:
        return render_template("contact.html", form=form, msg_status="<<Message Being Drafted.>>", recognition_web_template=recognition_web_template)

    except:  # An error has occurred.
        # Log error into system log file:
        update_system_log("route: '/contact'", traceback.format_exc())

        # Go to the web page which displays error details to the user:
        return render_template("error.html", activity="route: '/contact'", details=traceback.format_exc())


# Configure route for "Delete Cafe (confirm)" web page:
@app.route('/delete_cafe_confirm/<cafe_id>')
def delete_cafe_confirm(cafe_id):
    global db, app

    try:
        # Initialize variables to track whether the desired cafe record has been successfully obtained or if an error has occurred:
        success=False
        error_msg= ""

        # Query the database for information on desired cafe.  Capture feedback to relay to enf user:
        selected_cafe = retrieve_from_database("get_cafe_by_id", cafe_id=cafe_id)
        if selected_cafe == {}:
            error_msg = "An error has occurred. Cafe information cannot be obtained at this time."
        elif selected_cafe == []:
            error_msg = "No matching records were retrieved."
        else:
            # Indicate that record retrieval has been successfully executed:
            success = True

        # Go to the "Delete Cafe (confirm)" web page:
        return render_template("delete_cafe_confirm.html", cafe=selected_cafe, success=success, error_msg=error_msg, recognition_web_template=recognition_web_template)

    except:  # An error has occurred.
        # Log error into system log file:
        update_system_log("route: '/delete_cafe_confirm'", traceback.format_exc())

        # Go to the web page which displays error details to the user:
        return render_template("error.html", activity="route: '/delete_cafe_confirm'", details=traceback.format_exc())


# Configure route for "Delete Cafe (result)" web page:
@app.route('/delete_cafe_result/<cafe_id>')
def delete_cafe_result(cafe_id):
    global db, app

    try:
        # Delete the desired cafe record from the database.  Capture feedback to relay to end user:
        if not update_database("delete_cafe", item_to_process=[], cafe_id=cafe_id):
            result = "An error has occurred. Cafe has not been deleted."
        else:
            result = "Cafe has been successfully deleted."

        # Go to the web page to render the results:
        return render_template("db_update_result.html", trans_type="Delete", result=result, recognition_web_template=recognition_web_template)

    except:  # An error has occurred.
        # Log error into system log file:
        update_system_log("route: '/delete_cafe_result'", traceback.format_exc())

        # Go to the web page which displays error details to the user:
        return render_template("error.html", activity="route: '/delete_cafe_result'", details=traceback.format_exc())


# Configure route for "Edit Cafe" web page:
@app.route('/edit_cafe/<cafe_id>',methods=["GET", "POST"])
def edit_cafe(cafe_id):
    global db, app

    try:
        # Instantiate an instance of the "AddOrEditCafeForm" class:
        form = AddOrEditCafeForm()

        if form.validate_on_submit():
            # Initialize variable to summarize end result of this transaction attempt:
            result = ""

            # Initialize variable to track whether database update should proceed or not:
            update_db = False

            # Initialize variable to track whether cafe name has violated the unique-value constraint:
            unique_cafe_name_violation = False

            # Check if name of new cafe already exists in the db. Capture feedback to relay to enf user:
            cafe_name_in_db = retrieve_from_database("get_cafe_by_name", cafe_name=form.txt_name.data)
            if cafe_name_in_db == {}:
                result = "An error has occurred. Cafe has not been added."
            else:
                if cafe_name_in_db != None:
                    if cafe_name_in_db.id != int(cafe_id):
                        result = f"Cafe name '{form.txt_name.data}' already exists in the database.  Please go back and enter a unique cafe name."
                        unique_cafe_name_violation = True
                    else:
                        # Indicate that database update can proceed:
                        update_db = True
                else:
                    # Indicate that database update can proceed:
                    update_db = True

                # If database update can proceed, then do so:
                if update_db:
                    # Update the desired cafe record in the database.  Capture feedback to relay to end user:
                    if not update_database("update_cafe", form=form, cafe_id=cafe_id):
                        result = "An error has occurred. Cafe has not been updated."
                    else:
                        result = "Cafe has been successfully updated."

            # Go to the web page to render the results:
            return render_template("db_update_result.html", unique_cafe_name_violation=unique_cafe_name_violation, trans_type="Edit", result=result, recognition_web_template=recognition_web_template)

        # Initialize variables to track whether a record for the selected cafe was successfully obtained or if an error has occurred:
        success = False
        error_msg = ""

        # Get information from the database for the selected cafe. Capture feedback to relay to enf user:
        selected_cafe = retrieve_from_database("get_cafe_by_id", cafe_id=cafe_id)
        if selected_cafe == {}:
            error_msg = "An error has occurred. Cafe information cannot be obtained at this time."
        elif selected_cafe == []:
            error_msg = "No matching records were retrieved."
        else:
            # Populate the form with the retrieved record's contents:
            form.txt_name.data = selected_cafe.name
            form.txt_map_url.data = selected_cafe.map_url
            form.txt_img_url.data = selected_cafe.img_url
            form.txt_location.data = selected_cafe.location
            form.txt_has_sockets.data = selected_cafe.has_sockets
            form.txt_has_toilet.data = selected_cafe.has_toilet
            form.txt_has_wifi.data = selected_cafe.has_wifi
            form.txt_can_take_calls.data = selected_cafe.can_take_calls
            form.txt_seats.data = selected_cafe.seats
            form.txt_coffee_price.data = selected_cafe.coffee_price
            form.button_submit.label.text = "Update Cafe"

            # Indicate that record retrieval and form population have been successful:
            success = True

        # Go to the "Edit Cafe" web page:
        return render_template("edit_cafe.html", form=form, cafe=selected_cafe, success=success, error_msg=error_msg, recognition_web_template=recognition_web_template)

    except:  # An error has occurred.
        # Log error into system log file:
        update_system_log("route: '/edit_cafe'", traceback.format_exc())

        # Go to the web page which displays error details to the user:
        return render_template("error.html", activity="route: '/edit_cafe'", details=traceback.format_exc())


# DEFINE FUNCTIONS TO BE USED FOR THIS APPLICATION (LISTED IN ALPHABETICAL ORDER BY FUNCTION NAME):
# *************************************************************************************************
def config_database():
    """Function for configuring the database tables supporting this website"""
    global db, app, Cafes

    try:
        # Create the database object using the SQLAlchemy constructor:
        db = SQLAlchemy(model_class=Base)

        # Initialize the app with the extension:
        db.init_app(app)

        # Configure database tables (listed in alphabetical order; class names are sufficiently descriptive):
        class Cafes(db.Model):
            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
            map_url: Mapped[str] = mapped_column(String(500), nullable=False)
            img_url: Mapped[str] = mapped_column(String(500), nullable=False)
            location: Mapped[str] = mapped_column(String(250), nullable=False)
            has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
            has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
            has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
            can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
            seats: Mapped[str] = mapped_column(String(250), nullable=True)
            coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

        # Configure the database per the above.  If needed tables do not already exist in the DB, create them:
        with app.app_context():
            db.create_all()

        # At this point, function is presumed to have executed successfully.  Return
        # successful-execution indication to the calling function:
        return True

    except:  # An error has occurred.
        update_system_log("config_database", traceback.format_exc())

        # Return failed-execution indication to the calling function:
        return False


def config_web_forms():
    """Function for configuring the web forms supporting this website"""
    global AddOrEditCafeForm, ContactForm

    try:
        # CONFIGURE WEB FORMS (LISTED IN ALPHABETICAL ORDER):
        # Configure 'add/edit cafe' form:
        class AddOrEditCafeForm(FlaskForm):
            txt_name = StringField(label="Cafe Name:", validators=[InputRequired(), Length(max=250)])
            txt_map_url = StringField(label="Map URL:", validators=[InputRequired(), URL(), Length(max=500)])
            txt_img_url = StringField(label="Image URL:", validators=[InputRequired(), URL(), Length(max=500)])
            txt_location = StringField(label="Location:", validators=[InputRequired(), Length(max=250)])
            txt_has_sockets = BooleanField(label="Has sockets?:")
            txt_has_toilet = BooleanField(label="Has toilets?:")
            txt_has_wifi = BooleanField(label="Has WiFi?:")
            txt_can_take_calls = BooleanField(label="Can take calls?:")
            txt_seats = StringField(label="Seats:", validators=[Length(max=250)])
            txt_coffee_price = StringField(label="Coffee Price:", validators=[Length(max=250)])
            button_submit = SubmitField(label="Add Cafe")

        # Configure 'contact us' form:
        class ContactForm(FlaskForm):
            txt_name = StringField(label="Your Name:", validators=[InputRequired(), Length(max=50)])
            txt_email = EmailField(label="Your E-mail Address:", validators=[InputRequired(), Email()])
            txt_message = TextAreaField(label="Your Message:", validators=[InputRequired()])
            button_submit = SubmitField(label="Send Message")

        # At this point, function is presumed to have executed successfully.  Return\
        # successful-execution indication to the calling function:
        return True

    except:  # An error has occurred.
        update_system_log("config_web_forms", traceback.format_exc())

        # Return failed-execution indication to the calling function:
        return False


def email_from_contact_page(form):
    """Function to process a message that user wishes to e-mail from this website to the website administrator."""
    global SENDER_EMAIL_GMAIL, SENDER_HOST, SENDER_PASSWORD_GMAIL, SENDER_PORT
    try:
        # E-mail the message using the contents of the "Contact Us" web page form as input:
        with smtplib.SMTP(SENDER_HOST, port=SENDER_PORT) as connection:
            try:
                # Make connection secure, including encrypting e-mail.
                connection.starttls()
            except:
                # Return failed-execution message to the calling function:
                return "Error: Could not make connection to send e-mails. Your message was not sent."
            try:
                # Login to sender's e-mail server:
                connection.login(SENDER_EMAIL_GMAIL, SENDER_PASSWORD_GMAIL)
            except:
                # Return failed-execution message to the calling function:
                return "Error: Could not log into e-mail server to send e-mails. Your message was not sent."
            else:
                # Send e-mail:
                connection.sendmail(
                    from_addr=SENDER_EMAIL_GMAIL,
                    to_addrs=SENDER_EMAIL_GMAIL,
                    msg=f"Subject: Cafe and Wifi Website - E-mail from 'Contact Us' page\n\nName: {form.txt_name.data}\nE-mail address: {form.txt_email.data}\n\nMessage:\n{form.txt_message.data}"
                )
                # Return successful-execution message to the calling function:
                return "Your message has been successfully sent."

    except:  # An error has occurred.
        update_system_log("email_from_contact_page", traceback.format_exc())

        # Return failed-execution message to the calling function:
        return "An error has occurred. Your message was not sent."


def retrieve_from_database(trans_type, **kwargs):
    """Function to retrieve data from this application's database based on the type of transaction"""
    global app, db

    try:
        with app.app_context():
            if trans_type == "get_all_cafes":
                # Retrieve and return all existing cafes, sorted by name, from the "cafes" database table:
                return db.session.execute(db.select(Cafes).order_by(Cafes.name)).scalars().all()

            elif trans_type == "get_cafe_by_id":
                # Capture optional argument:
                cafe_id = kwargs.get("cafe_id", None)

                # Retrieve and return the record for the desired ID:
                return db.session.execute(db.select(Cafes).where(Cafes.id == cafe_id)).scalar()

            elif trans_type == "get_cafe_by_name":
                # Capture optional argument:
                cafe_name = kwargs.get("cafe_name", None)

                # Retrieve and return the record for the desired cafe name:
                return db.session.execute(db.select(Cafes).where(Cafes.name == cafe_name)).scalar()

    except:  # An error has occurred.
        update_system_log("retrieve_from_database (" + trans_type + ")", traceback.format_exc())

        # Return empty dictionary as a failed-execution indication to the calling function:
        return {}


def run_app():
    """Main function for this application"""
    global app

    try:
        # Load environmental variables from the ".env" file:
        load_dotenv()

        # Configure the SQLite database, relative to the app instance folder:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cafes.db"

        # Initialize an instance of Bootstrap5, using the "app" object defined above as a parameter:
        Bootstrap5(app)

        # Retrieve the secret key to be used for CSRF protection:
        app.secret_key = os.getenv("SECRET_KEY_FOR_CSRF_PROTECTION")

        # Configure database tables.  If function failed, update system log and return
        # failed-execution indication to the calling function:
        if not config_database():
            update_system_log("run_app", "Error: Database configuration failed.")
            return False

        # Configure web forms.  If function failed, update system log and return
        # failed-execution indication to the calling function:
        if not config_web_forms():
            update_system_log("run_app", "Error: Web forms configuration failed.")
            return False

    except:  # An error has occurred.
        update_system_log("run_app", traceback.format_exc())
        return False


def update_database(trans_type, **kwargs):
    """Function to update this application's database based on the type of transaction"""
    try:
        with app.app_context():
            if trans_type == "add_cafe":
                # Capture optional argument:
                form = kwargs.get("form", None)

                # Upload, to the "cafes" database table, contents of the form passed to this function:
                new_records = []

                new_record = Cafes(
                    name=form.txt_name.data,
                    map_url=form.txt_map_url.data,
                    img_url=form.txt_img_url.data,
                    location=form.txt_location.data,
                    has_sockets=form.txt_has_sockets.data,
                    has_toilet=form.txt_has_toilet.data,
                    has_wifi=form.txt_has_wifi.data,
                    can_take_calls=form.txt_can_take_calls.data,
                    seats=form.txt_seats.data,
                    coffee_price=form.txt_coffee_price.data
                )
                new_records.append(new_record)

                db.session.add_all(new_records)
                db.session.commit()

            elif trans_type == "delete_cafe":
                # Capture optional argument:
                cafe_id = kwargs.get("cafe_id", None)

                # Delete the record associated with the selected ID:
                db.session.query(Cafes).where(Cafes.id == cafe_id).delete()
                db.session.commit()

            elif trans_type == "update_cafe":
                # Capture optional arguments:
                form = kwargs.get("form", None)
                cafe_id = kwargs.get("cafe_id", None)

                # Update record for the selected ID:
                record_to_update = db.session.query(Cafes).filter(Cafes.id == cafe_id).first()
                record_to_update.name = form.txt_name.data
                record_to_update.map_url = form.txt_map_url.data
                record_to_update.img_url = form.txt_img_url.data
                record_to_update.location = form.txt_location.data
                record_to_update.has_sockets = form.txt_has_sockets.data
                record_to_update.has_toilet = form.txt_has_toilet.data
                record_to_update.has_wifi = form.txt_has_wifi.data
                record_to_update.can_take_calls = form.txt_can_take_calls.data
                record_to_update.seats = form.txt_seats.data
                record_to_update.coffee_price = form.txt_coffee_price.data

                db.session.commit()

        # Return successful-execution indication to the calling function:
        return True

    except:  # An error has occurred.
        update_system_log("update_database (" + trans_type + ")", traceback.format_exc())

        # Return failed-execution indication to the calling function:
        return False


def update_system_log(activity, log):
    """Function to update the system log with errors encountered"""
    global dlg

    try:
        # Capture current date/time:
        current_date_time = datetime.now()
        current_date_time_file = current_date_time.strftime("%Y-%m-%d")

        # Update log file.  If log file does not exist, create it:
        with open("log_cafe_and_wifi_website_" + current_date_time_file + ".txt", "a") as f:
            f.write(datetime.now().strftime("%Y-%m-%d @ %I:%M %p") + ":\n")
            f.write(activity + ": " + log + "\n")

        # Close the log file:
        f.close()

    except:
        dlg = wx.App()
        dlg = wx.MessageBox(f"Error: System log could not be updated.\n{traceback.format_exc()}", 'Error', wx.OK | wx.ICON_INFORMATION)


# Run main function for this application:
run_app()

# Destroy the object that was created to show user dialog and message boxes:
dlg.Destroy()

if __name__ == "__main__":
    app.run(debug=True, port=5003)