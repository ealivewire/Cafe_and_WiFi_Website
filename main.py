# PROFESSIONAL PROJECT: Cafe and WiFi Website

# OBJECTIVE: To implement a website offering users a way to add, edit, and view information on cafes and their amenities.

# Import necessary library(ies):
from data import app, db, recognition_web_template,  SENDER_EMAIL_GMAIL, SENDER_HOST, SENDER_PASSWORD_GMAIL, SENDER_PORT
from data import Cafes, AddOrEditCafeForm, ContactForm
from datetime import datetime
from dotenv import load_dotenv
import email_validator
from flask import Flask, jsonify, render_template, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
import os
import requests
import smtplib
from sqlalchemy import Boolean, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import traceback
import validators
from wtforms.validators import InputRequired, Length, Email, URL
from wtforms import BooleanField, EmailField, StringField, SubmitField, TextAreaField
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
    try:
        # Go to the "About" page:
        return render_template("about.html", recognition_web_template=recognition_web_template)

    except:
        # Log error into system log file:
        update_system_log("route: '/about'", traceback.format_exc())

        # Go to the web page which displays error details to the user:
        return render_template("error.html", activity="route: '/about'", details=traceback.format_exc())


# Configure route for "add cafe" web page:
@app.route('/add_cafe',methods=["GET", "POST"])
def add_cafe():
    try:
        # Instantiate an instance of the "AddOrEditCafeForm" class:
        form = AddOrEditCafeForm()

        # If form-level validation has passed, perform additional processing:
        if form.validate_on_submit():
            # Initialize variable to summarize end result of this transaction attempt:
            result = ""

            # Initialize variable to track whether cafe name has violated the unique-value constraint:
            unique_cafe_name_violation = False

            # Check if name of new cafe already exists in the db.  Capture feedback to relay to end user:
            cafe_name_in_db = retrieve_from_database("get_cafe_by_name", cafe_name=form.txt_name.data)
            if cafe_name_in_db == {}:
                result = "An error has occurred. Cafe has not been added."
            elif cafe_name_in_db != None:
                result = f"Cafe name '{form.txt_name.data}' already exists in the database.  Please go back and enter a unique cafe name."
                unique_cafe_name_violation = True
            else:
                # Add the new cafe record from the database.  Capture feedback to relay to end user:
                if not update_database("add_cafe_via_web", form=form):
                    result = "An error has occurred. Cafe has not been added."
                else:
                    result = "Cafe has been successfully added."

            # Go to the web page to render the results:
            return render_template("db_update_result.html", unique_cafe_name_violation=unique_cafe_name_violation, trans_type="Add", result=result,
                                   recognition_web_template=recognition_web_template)

        # Go to the "add cafe" web page:
        return render_template("add_cafe.html", form=form, recognition_web_template=recognition_web_template)

    except:  # An error has occurred.
        # Log error into system log file:
        update_system_log("route: '/add_cafe'", traceback.format_exc())

        # Go to the web page which displays error details to the user:
        return render_template("error.html", activity="route: '/add_cafe'", details=traceback.format_exc())


# Configure route for "existing cafes" web page:
@app.route('/cafes')
def cafes():
    try:
        # Initialize variables to track whether existing cafe records were successfully obtained or if an error has occurred:
        success = False
        error_msg = ""
        cafe_count = 0

        # Get information on existing cafes in the database. Capture feedback to relay to end user:
        existing_cafes = retrieve_from_database("get_all_cafes")
        if existing_cafes == {}:
            error_msg = "An error has occurred. Cafe information cannot be obtained at this time."
        elif existing_cafes == []:
            error_msg = "No matching records were retrieved."
        else:
            cafe_count = len(existing_cafes)  # Record count to be displayed in the sub-header of the "existing cafes" web page.

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
    try:
        # Initialize variables to track whether the desired cafe record has been successfully obtained or if an error has occurred:
        success=False
        error_msg= ""

        # Query the database for information on desired cafe.  Capture feedback to relay to end user:
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
    try:
        # Delete the desired cafe record from the database.  Capture feedback to relay to end user:
        if not update_database("delete_cafe_by_id_via_web", cafe_id=cafe_id):
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


# Configure route for "edit cafe" web page:
@app.route('/edit_cafe/<cafe_id>',methods=["GET", "POST"])
def edit_cafe(cafe_id):
    try:
        # Instantiate an instance of the "AddOrEditCafeForm" class:
        form = AddOrEditCafeForm()

        # If form-level validation has passed, perform additional processing:
        if form.validate_on_submit():
            # Initialize variable to summarize end result of this transaction attempt:
            result = ""

            # Initialize variable to track whether database update should proceed or not:
            update_db = False

            # Initialize variable to track whether cafe name has violated the unique-value constraint:
            unique_cafe_name_violation = False

            # Check if name of new cafe already exists in the db. Capture feedback to relay to end user:
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
                    if not update_database("edit_cafe_via_web", form=form, cafe_id=cafe_id):
                        result = "An error has occurred. Cafe has not been edited."
                    else:
                        result = "Cafe has been successfully edited."

            # Go to the web page to render the results:
            return render_template("db_update_result.html", unique_cafe_name_violation=unique_cafe_name_violation, trans_type="Edit", result=result, recognition_web_template=recognition_web_template)

        # Initialize variables to track whether a record for the selected cafe was successfully obtained or if an error has occurred:
        success = False
        error_msg = ""

        # Get information from the database for the selected cafe. Capture feedback to relay to end user:
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


# CONFIGURE ROUTES FOR HANDLING DATABASE REQUESTS VIA API (LISTED IN ALPHABETICAL ORDER BY ROUTE NAME):
# ***********************************************************************************************************
# Configure route to add cafe via API:
@app.route("/add", methods=["POST"])
def add_cafe_via_api():
    # Check if the request method is appropriate:
    if request.method == "POST":
        try:
            # Capture data received from the API request and store in a dictionary:
            data_received = {}
            for key in request.form:
                data_received[key] = request.form[key]

        except:
            return jsonify(
                result={"invalid_request": "Data to add was not received as part of the API request."}), 404

        # At this point, JSON has been received:
        try:
            # Validate data in JSON to see if it meets all database requirements:
            validated, error_json = validate_add_from_api(data_received)
            if not validated:
                return error_json, 404

            # At this point, JSON has been successfully validated.
            # Add the new cafe record from the database.  Capture feedback to relay to end user:
            if not update_database("add_cafe_via_api", data=data_received):
                return jsonify(
                    result={"error": "An error has occurred in adding cafe to database."}), 404

            else:
                return jsonify(
                    result={"success": f"Cafe '{data_received["name"]}' has been successfully added."}), 200

        except:
            return jsonify(
                result={"error": "An error has occurred.  Cafe information cannot be added at this time."}), 404

    else:
        return jsonify(result={"invalid_request": "Invalid API request method."}), 404


# Configure route to get a listing of all cafes via API:
@app.route("/all/", methods=["GET"])
def get_all_cafes_via_api():
    if request.method == "GET":
        try:
            # Retrieve information for all cafes in the database.  Return resulting JSON to user:
            selected_cafes = retrieve_from_database("get_all_cafes")
            if selected_cafes == {}:  # An error occurred while attempting to retrieve qualifying records.
                return jsonify(
                    result={"error": "An error has occurred.  Cafe information cannot be provided at this time."}), 404

            elif selected_cafes == []:  # No qualifying records were retrieved.
                return jsonify(
                    result={"no_records_found": "Sorry, no records were found which satisfy the API request."}), 404

            else:  # At least one qualifying record was obtained from the database.
                return jsonify(cafes=[cafe.to_dict() for cafe in selected_cafes]), 200

        except:  # An error has occurred.
            return jsonify(
                result={"error": "An error has occurred.  Cafe information cannot be provided at this time."}), 404

    else:
        return jsonify(
            result={"invalid_request": "Invalid API request method."}), 404


# Configure route to delete, from the database and via API, cafe of a particular name:
@app.route("/delete", methods=["GET", "DELETE"])
def delete_cafe_by_name_via_api():
    try:
        # Capture the cafe name ("cafe_name") parameter that user has provided via the API request.
        # If no cafe name was provided, return feedback to user:
        cafe_name = request.args.get("name")
        if cafe_name == None or cafe_name == "":
            return jsonify(result={"invalid_request": "No cafe name was received for this request."}), 404

        # Query the database for the desired cafe record.  Return resulting JSON to user:
        selected_cafe = retrieve_from_database("get_cafe_by_name", cafe_name=cafe_name)
        if selected_cafe == {}:  # An error occurred while attempting to retrieve qualifying record.
            return jsonify(
                result={"error": "An error has occurred.  Cafe information cannot be provided at this time."}), 404

        elif selected_cafe == None:  # No qualifying records were retrieved.
            return jsonify(
                result={"no_records_found": "Sorry, no records were found which satisfy the API request."}), 404

        else:  # Qualifying record was obtained from the database.
            # Delete the desired cafe record from the database.  Return resulting JSON to user:
            if not update_database("delete_cafe_by_name_via_api", cafe_name=cafe_name):
                return jsonify(result={"error": "An error has occurred.  Cafe cannot be deleted at this time."}), 404
            else:
                return jsonify(result={"success": "Cafe has been successfully deleted."}), 200

    except:  # An error has occurred.
        return jsonify(result={"error": "An error has occurred.  Cafe cannot be deleted at this time."}), 404


# Configure route to edit cafe via API:
@app.route("/edit", methods=["POST"])
def edit_cafe_via_api():
    # Check if the request method is appropriate:
    if request.method == "POST":
        try:
            # Capture data received from the API request and store in a dictionary:
            data_received = {}
            for key in request.form:
                data_received[key] = request.form[key]


        except:
            return jsonify(
                result={"invalid_request": "Data to edit was not received as part of the API request."}), 404

        # At this point, JSON has been received:
        try:
            # Validate data in JSON to see if it meets all database requirements:
            validated, error_json = validate_edit_from_api(data_received)
            if not validated:
                return error_json, 404

            # At this point, JSON has been successfully validated.
            # Edit the cafe record in the database.  Capture feedback to relay to end user:
            if not update_database("edit_cafe_via_api", data=data_received):
                return jsonify(
                    result={"error": "An error has occurred in editing cafe in database."}), 404

            else:
                return jsonify(
                    result={"success": f"Cafe '{data_received["name"]}' has been successfully edited."}), 200

        except:
            return jsonify(
                result={"error": "An error has occurred.  Cafe information cannot be edited at this time."}), 404

    else:
        return jsonify(
            result={"invalid_request": "Invalid API request method."}), 404


# Configure route to rename cafe via API:
@app.route("/rename", methods=["POST"])
def rename_cafe_via_api():
    # Check if the request method is appropriate:
    if request.method == "POST":
        try:
            # Capture data received from the API request and store in a dictionary:
            data_received = {}
            for key in request.form:
                data_received[key] = request.form[key]

        except:
            return jsonify(
                result={"invalid_request": "Data to rename was not received as part of the API request."}), 404

        # At this point, JSON has been received:
        try:
            # Validate data in JSON to see if it meets all database requirements:
            validated, error_json = validate_rename_from_api(data_received)
            if not validated:
                return error_json, 404

            # At this point, JSON has been successfully validated.
            # Rename the cafe record in the database.  Capture feedback to relay to end user:
            if not update_database("rename_cafe_via_api", data=data_received):
                return jsonify(
                    result={"error": "An error has occurred in renaming cafe in database."}), 404

            else:
                return jsonify(
                    result={"success": f"Cafe '{data_received["name_old"]}' has been successfully renamed to '{data_received["name_new"]}'."}), 200

        except:
            return jsonify(
                result={"error": "An error has occurred.  Cafe cannot be renamed at this time."}), 404

    else:
        return jsonify(
            result={"invalid_request": "Invalid API request method."}), 404


# Configure route to search for cafes at a particular location via API:
@app.route("/search", methods=["GET"])
def get_cafes_by_location_via_api():
    if request.method == "GET":
        try:
            # Capture the location ("loc") parameter that user has provided via the API request.
            # If no location was provided, return feedback to user:
            loc = request.args.get("loc")
            if loc == None or loc == "":
                return jsonify(result={"invalid_request": "No location was received for this request."}), 404

            # Retrieve information for cafes located at the desired location.  Return resulting JSON to user:
            selected_cafes = retrieve_from_database("get_cafes_by_location", loc=loc)
            if selected_cafes == {}:  # An error occurred while attempting to retrieve qualifying records.
                return jsonify(
                    result={"error": "An error has occurred.  Cafe information cannot be provided at this time."}), 404

            elif selected_cafes == []:  # No qualifying records were retrieved.
                return jsonify(
                    result={"no_records_found": "Sorry, no records were found which satisfy the API request."}), 404

            else:  # At least one qualifying record was obtained from the database.
                return jsonify(cafes=[cafe.to_dict() for cafe in selected_cafes]), 200

        except:  # An error has occurred.
            return jsonify(
                result={"error": "An error has occurred.  Cafe information cannot be provided at this time."}), 404

    else:
        return jsonify(
            result={"invalid_request": "Invalid API request method."}), 404


# CONFIGURE ROUTES FOR **TESTING** FOR PROPER API RESPONSE TO DATABASE REQUESTS (LISTED IN ALPHABETICAL ORDER BY ROUTE NAME):
# ***************************************************************************************************************************
# # Configure route to test API response to "add cafe" requests:
# @app.route("/test_add")
# def test_add():
#     # Prepare the dictionary with data for the new cafe to be added:
#     data = {
#         "name": "The other new place in town2",
#         "map_url": "http://www.zzz.com",
#         "img_url": "http://www.xxx.com",
#         "location": "Anywhere",
#         "has_sockets": False,
#         "has_toilet": False,
#         "has_wifi": 0,
#         "can_take_calls": 1,
#         "seats": "30,000+",
#         "coffee_price": "$50.21"
#     }
#
#     # Store an invalid dictionary in the variable to be submitted with the API request:
#     # data = []
#
#     # Submit the API request:
#     data = requests.post("http://127.0.0.1:5003/add", data=data)
#
#     # Test an API request with a missing data dictionary:
#     # data = requests.post("http://127.0.0.1:5003/add")
#
#     # Return the results:
#     return data.json()
#
#
# # Configure route to test API response to "edit cafe" requests:
# @app.route("/test_edit")
# def test_edit():
#     # Prepare the dictionary with data for the new cafe to be edited:
#     data = {
#         "name": "Pizza Village 11",
#         "map_url": "http://www.ooo.com",
#         "img_url": "http://www.qqq.com",
#         "location": "Cleveland",
#         "has_sockets": 0,
#         "has_toilet": 1,
#         "has_wifi": True,
#         "can_take_calls": False,
#         "seats": "Enough",
#         "coffee_price": "Ultra Expensive"
#     }
#
#     # Store an invalid JSON in the variable to be submitted with the API request:
#     # data = []
#
#     # Submit the API request:
#     data = requests.post("http://127.0.0.1:5003/edit", data=data)
#
#     # Test an API request with a missing JSON:
#     # data = requests.post("http://127.0.0.1:5003/edit")
#
#     # Return the results:
#     return data.json()
#
#
# # Configure route to test API response to "rename cafe" requests:
# @app.route("/test_rename")
# def test_rename():
#     # Prepare the dictionary with data for the new cafe to be edited:
#     data = {
#         "name_old": "pizza village 16",
#         "name_new": "PIZza village 19",
#         # "coffee_price": "$3.45"
#     }
#
#     # Store an invalid JSON in the variable to be submitted with the API request:
#     # data = []
#
#     # Submit the API request:
#     data = requests.post("http://127.0.0.1:5003/rename", data=data)
#
#     # Test an API request with a missing JSON:
#     # data = requests.post("http://127.0.0.1:5003/rename")
#
#     # Return the results:
#     return data.json()


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

            # Create method to convert cafe data to a dictionary:
            def to_dict(self):
                # Method 1.
                dictionary = {}
                # Loop through each column in the data record
                for column in self.__table__.columns:
                    # Create a new dictionary entry where the key is the name of the column and the value is the value of the column:
                    dictionary[column.name] = getattr(self, column.name)
                return dictionary

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
                return "error: Could not make connection to send e-mails. Your message was not sent."
            try:
                # Login to sender's e-mail server:
                connection.login(SENDER_EMAIL_GMAIL, SENDER_PASSWORD_GMAIL)
            except:
                # Return failed-execution message to the calling function:
                return "error: Could not log into e-mail server to send e-mails. Your message was not sent."
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
                return db.session.execute(db.select(Cafes).order_by(func.lower(Cafes.name))).scalars().all()

            elif trans_type == "get_cafe_by_id":
                # Capture optional argument:
                cafe_id = kwargs.get("cafe_id", None)

                # Retrieve and return the record for the desired ID:
                return db.session.execute(db.select(Cafes).where(Cafes.id == cafe_id)).scalar()

            elif trans_type == "get_cafe_by_name":
                # Capture optional argument:
                cafe_name = kwargs.get("cafe_name", None)

                # Retrieve and return the record for the desired cafe name:
                return db.session.execute(db.select(Cafes).where(Cafes.name.ilike(cafe_name))).scalar()

            elif trans_type == "get_cafes_by_location":
                # Capture optional argument:
                loc = kwargs.get("loc", None)

                # Retrieve and return the cafe records for the desired location:
                return db.session.execute(db.select(Cafes).where(Cafes.location.ilike(loc))).scalars().all()

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
            if trans_type == "add_cafe_via_api":
                # Capture optional argument:
                data = kwargs.get("data", None)

                # Upload, to the "cafes" database table, contents of the "data" parameter passed to this function:
                new_records = []

                new_record = Cafes(
                    name=data["name"],
                    map_url=data["map_url"],
                    img_url=data["img_url"],
                    location=data["location"],
                    has_sockets=data["has_sockets"],
                    has_toilet=data["has_toilet"],
                    has_wifi=data["has_wifi"],
                    can_take_calls=data["can_take_calls"],
                    seats=data["seats"],
                    coffee_price=data["coffee_price"]
                )
                new_records.append(new_record)

                db.session.add_all(new_records)
                db.session.commit()

            elif trans_type == "add_cafe_via_web":
                # Capture optional argument:
                form = kwargs.get("form", None)

                # Upload, to the "cafes" database table, contents of the "form" parameter passed to this function:
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

            elif trans_type == "delete_cafe_by_id_via_web":
                # Capture optional argument:
                cafe_id = kwargs.get("cafe_id", None)

                # Delete the record associated with the selected ID:
                db.session.query(Cafes).where(Cafes.id == cafe_id).delete()
                db.session.commit()

            elif trans_type == "delete_cafe_by_name_via_api":
                # Capture optional argument:
                cafe_name = kwargs.get("cafe_name", None)

                # Delete the record associated with the selected name:
                db.session.query(Cafes).where(Cafes.name.ilike(cafe_name)).delete()
                db.session.commit()

            elif trans_type == "edit_cafe_via_api":
                # Capture optional argument:
                data = kwargs.get("data", None)

                # Edit record for the desired cafe (for fields indicated in the "data" parameter passed to this function):
                record_to_edit = db.session.query(Cafes).filter(Cafes.name.ilike(data["name"])).first()

                if "map_url" in data.keys():
                    record_to_edit.map_url = data["map_url"]
                if "img_url" in data.keys():
                    record_to_edit.img_url = data["img_url"]
                if "location" in data.keys():
                    record_to_edit.location = data["location"]
                if "has_sockets" in data.keys():
                    record_to_edit.has_sockets = data["has_sockets"]
                if "has_toilet" in data.keys():
                    record_to_edit.has_toilet = data["has_toilet"]
                if "has_wifi" in data.keys():
                    record_to_edit.has_wifi = data["has_wifi"]
                if "can_take_calls" in data.keys():
                    record_to_edit.can_take_calls = data["can_take_calls"]
                if "seats" in data.keys():
                    record_to_edit.seats = data["seats"]
                if "coffee_price" in data.keys():
                    record_to_edit.coffee_price = data["coffee_price"]

                db.session.commit()

            elif trans_type == "edit_cafe_via_web":
                # Capture optional arguments:
                form = kwargs.get("form", None)
                cafe_id = kwargs.get("cafe_id", None)

                # Edit record for the selected ID, using data in the "form" parameter passed to this function:
                record_to_edit = db.session.query(Cafes).filter(Cafes.id == cafe_id).first()
                record_to_edit.name = form.txt_name.data
                record_to_edit.map_url = form.txt_map_url.data
                record_to_edit.img_url = form.txt_img_url.data
                record_to_edit.location = form.txt_location.data
                record_to_edit.has_sockets = form.txt_has_sockets.data
                record_to_edit.has_toilet = form.txt_has_toilet.data
                record_to_edit.has_wifi = form.txt_has_wifi.data
                record_to_edit.can_take_calls = form.txt_can_take_calls.data
                record_to_edit.seats = form.txt_seats.data
                record_to_edit.coffee_price = form.txt_coffee_price.data

                db.session.commit()

            elif trans_type == "rename_cafe_via_api":
                # Capture optional argument:
                data = kwargs.get("data", None)

                # Rename the desired cafe:
                cafe_to_rename = db.session.query(Cafes).filter(Cafes.name.ilike(data["name_old"])).first()
                cafe_to_rename.name = data["name_new"]

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
        dlg = wx.MessageBox(f"Error: System log could not be updated.\n{traceback.format_exc()}", 'Error',
                            wx.OK | wx.ICON_INFORMATION)


def validate_add_from_api(data):
    """Function to check if all fields in an API "add cafe" request meet database requirements prior to updating the database"""
    try:
        # Define (via a list) which fields are REQUIRED to be accounted for in the API request:
        required_fields = ["name", "map_url", "img_url", "location", "has_sockets", "has_toilet", "has_wifi",
                           "can_take_calls"]

        # Define (via a list) which fields are OPTIONAL but can still be accepted from the API request:
        optional_fields = ["seats", "coffee_price"]

        try:
            # COMPARE FIELDS PROVIDED IN THE API REQUEST VS. THOSE THAT CAN EXPECTED BY THE API:
            # Capture which of the required fields have NOT been provided by the API request:
            required_fields_not_provided = [field for field in required_fields if not field in data.keys()]

            # Capture which of the fields provided by the API request are not either one of the
            # required or optional fields expected by the API:
            invalid_fields_provided = [field for field in data.keys() if not field in required_fields and not field in optional_fields]

            # Check if at least one required field was not accounted for in the API request.  If so,
            # return validation-failure feedback to the calling function:
            if len(required_fields_not_provided) > 0:
                return False, jsonify(result={
                    "validation_error": f"The following required fields were not provided in the API request: {required_fields_not_provided}."})

            # Check if at least one invalid field was provided in the API request.  If so,
            # return validation-failure feedback to the calling function:
            if len(invalid_fields_provided) > 0:
                return False, jsonify(result={
                    "validation_error": f"The following invalid fields were provided in the API request: {invalid_fields_provided}."})

            # VALIDATE EACH FIELD PROVIDED IN THE API REQUEST:
            # FIELD = name:
            # Check if field is of length > 0 and <= 250:
            if len(str(data["name"]).rstrip()) == 0 or len(str(data["name"]).rstrip()) > 250:
                return False, jsonify(result={
                    "validation_error": "Field 'name' must be populated and have length <= 250 characters."})

            # Check if field does not already exist in the database:
            cafe_name_in_db = retrieve_from_database("get_cafe_by_name", cafe_name=str(data["name"]))
            if cafe_name_in_db == {}:
                return False, jsonify(
                    result={"validation_error": "An error has occurred in validating fields for API request."})
            elif cafe_name_in_db != None:
                return False, jsonify(result={
                    "validation_error": f"Cafe name '{data["name"]}' already exists in the database."})

            # FIELD = location:
            # Check if field is of length > 0 and <= 250:
            if len(str(data["location"]).rstrip()) == 0 or len(str(data["location"]).rstrip()) > 250:
                return False, jsonify(result={
                    "validation_error": "Field 'location' must be populated and have length <= 250 characters."})

            # FIELD = map_url:
            # Check if field is of length > 0 and <= 500:
            if len(str(data["map_url"]).rstrip()) == 0 or len(str(data["map_url"]).rstrip()) > 500:
                return False, jsonify(result={
                    "validation_error": "Field 'map_url' must be populated and have length <= 500 characters."})

            # Check if field resembles a valid URL:
            if not validators.url(str(data["map_url"]).rstrip()):
                return False, jsonify(
                    result={"validation_error": "Field 'map_url' does not resemble a valid URL."})

            # FIELD = img_url:
            # Check if field is of length > 0 and <= 500:
            if len(str(data["img_url"]).rstrip()) == 0 or len(str(data["img_url"]).rstrip()) > 500:
                return False, jsonify(result={
                    "validation_error": "Field 'img_url' must be populated and have length <= 500 characters."})

            # Check if field resembles a valid URL:
            if not validators.url(str(data["img_url"]).rstrip()):
                return False, jsonify(
                    resultr={"validation_error": "Field 'img_url' does not resemble a valid URL."})

            # FIELD = has_sockets:
            # Convert string True/False/0/1 to integer equivalents:
            if data["has_sockets"] == "False" or data["has_sockets"] == "0":
                data["has_sockets"] = 0
            elif data["has_sockets"] == "True" or data["has_sockets"] == "1":
                data["has_sockets"] = 1

            # Check if field has a boolean value:
            if not (data["has_sockets"] == 0 or data["has_sockets"] == 1):
                return False, jsonify(result={
                    "validation_error": "Field 'has_sockets' must have a value of either 0, 1, False, or True (and without surrounding quotes)."})

            # FIELD = has_toilet:
            # Convert string True/False/0/1 to integer equivalents:
            if data["has_toilet"] == "False" or data["has_toilet"] == "0":
                data["has_toilet"] = 0
            elif data["has_toilet"] == "True" or data["has_toilet"] == "1":
                data["has_toilet"] = 1

            # Check if field has a boolean value:
            if not (data["has_toilet"] == 0 or data["has_toilet"] == 1):
                return False, jsonify(result={
                    "validation_error": "Field 'has_toilet' must have a value of either 0, 1, False, or True (and without surrounding quotes)."})

            # FIELD = has_wifi:
            # Convert string True/False/0/1 to integer equivalents:
            if data["has_wifi"] == "False" or data["has_wifi"] == "0":
                data["has_wifi"] = 0
            elif data["has_wifi"] == "True" or data["has_wifi"] == "1":
                data["has_wifi"] = 1

            # Check if field has a boolean value:
            if not (data["has_wifi"] == 0 or data["has_wifi"] == 1):
                return False, jsonify(result={
                    "validation_error": "Field 'has_wifi' must have a value of either 0, 1, False, or True (and without surrounding quotes)."})

            # FIELD = can_take_calls:
            # Convert string True/False/0/1 to integer equivalents:
            if data["can_take_calls"] == "False" or data["can_take_calls"] == "0":
                data["can_take_calls"] = 0
            elif data["can_take_calls"] == "True" or data["can_take_calls"] == "1":
                data["can_take_calls"] = 1

            # Check if field has a boolean value:
            if not (data["can_take_calls"] == 0 or data["can_take_calls"] == 1):
                return False, jsonify(result={
                    "validation_error": "Field 'can_take_calls' must have a value of either 0, 1, False, or True (and without surrounding quotes)."})

            # FIELD = seats (optional field; validate if provided):
            if "seats" in data.keys():
                # Check if field is of length <= 250:
                if len(str(data["seats"]).rstrip()) > 250:
                    return False, jsonify(
                        result={"validation_error": "Field 'seats' must have length <= 250 characters."})

            # FIELD = coffee_price (optional field; validate if provided):
            if "coffee_price" in data.keys():
                # Check if field is of length <= 250:
                if len(str(data["coffee_price"]).rstrip()) > 250:
                    return False, jsonify(result={
                        "validation_error": "Field 'coffee_price' must have length <= 250 characters."})

            # At this point, validation is deemed to have passed all validation checks.
            # Return successful-validation indication to the calling function
            # (Feedback JSON will not be returned, for final feedback will be deferred to the end
            # of processing the API request in full.):
            return True, ""

        except:
            return False, jsonify(
                result={"validation_error": f"An invalid JSON was provided in the API request."})

    except:  # An error has occurred:
        return False, jsonify(result={"validation_error": "An error has occurred in validating fields for API request."})


def validate_edit_from_api(data):
    """Function to check if all fields in an API "edit cafe" request meet database requirements prior to updating the database"""
    try:
        # Define (via a list) which fields are VALID and can be accepted from the API request:
        valid_fields = ["name", "map_url", "img_url", "location", "has_sockets", "has_toilet", "has_wifi","can_take_calls","seats","coffee_price"]

        try:
            # Check if "name" was provided in the API request:
            if "name" not in data.keys():
                return False, jsonify(result={
                    "validation_error": "Field 'name' is missing from the API request."})
            else:
                # Check if "name" field exists in the database:
                cafe_name_in_db = retrieve_from_database("get_cafe_by_name", cafe_name=str(data["name"]))
                if cafe_name_in_db == {}:
                    return False, jsonify(
                        result={"validation_error": "An error has occurred in validating fields for API request."})
                elif cafe_name_in_db == None:
                    return False, jsonify(result={
                        "validation_error": f"Cafe name '{data["name"]}' does not exist in the database."})

            # Check if at least one field has been identified for editing in the API request:
            fields_to_edit = [field for field in data.keys() if field in valid_fields and field != "name"]
            if len(fields_to_edit) == 0:
                return False, jsonify(result={
                    "validation_error": "No fields were listed in the API request as requiring editing."})

            # COMPARE FIELDS PROVIDED IN THE API REQUEST VS. THOSE THAT CAN EXPECTED BY THE API:
            # Capture which of the fields provided by the API request are not on the list of
            # valid fields expected by the API:
            invalid_fields_provided = [field for field in data.keys() if not field in valid_fields]

            # Check if at least one invalid field was provided in the API request.  If so,
            # return validation-failure feedback to the calling function:
            if len(invalid_fields_provided) > 0:
                return False, jsonify(result={
                    "validation_error": f"The following invalid fields were provided in the API request: {invalid_fields_provided}."})

            # VALIDATE EACH FIELD PROVIDED IN THE API REQUEST:
            # FIELD = name:
            # Check if field is of length > 0 and <= 250:
            if len(str(data["name"]).rstrip()) == 0 or len(str(data["name"]).rstrip()) > 250:
                return False, jsonify(result={
                    "validation_error": "Field 'name' must be populated and have length <= 250 characters."})

            # FIELD = location:
            if "location" in data.keys():
                # Check if field is of length > 0 and <= 250:
                if len(str(data["location"]).rstrip()) == 0 or len(str(data["location"]).rstrip()) > 250:
                    return False, jsonify(result={
                        "validation_error": "Field 'location' must be populated and have length <= 250 characters."})

            # FIELD = map_url:
            if "map_url" in data.keys():
                # Check if field is of length > 0 and <= 500:
                if len(str(data["map_url"]).rstrip()) == 0 or len(str(data["map_url"]).rstrip()) > 500:
                    return False, jsonify(result={
                        "validation_error": "Field 'map_url' must be populated and have length <= 500 characters."})

                # Check if field resembles a valid URL:
                if not validators.url(str(data["map_url"]).rstrip()):
                    return False, jsonify(
                        result={"validation_error": "Field 'map_url' does not resemble a valid URL."})

            # FIELD = img_url:
            if "img_url" in data.keys():
                # Check if field is of length > 0 and <= 500:
                if len(str(data["img_url"]).rstrip()) == 0 or len(str(data["img_url"]).rstrip()) > 500:
                    return False, jsonify(result={
                        "validation_error": "Field 'img_url' must be populated and have length <= 500 characters."})

                # Check if field resembles a valid URL:
                if not validators.url(str(data["img_url"]).rstrip()):
                    return False, jsonify(
                        resultr={"validation_error": "Field 'img_url' does not resemble a valid URL."})

            # FIELD = has_sockets:
            if "has_sockets" in data.keys():
                # Convert string True/False/0/1 to integer equivalents:
                if data["has_sockets"] == "False" or data["has_sockets"] == "0":
                    data["has_sockets"] = 0
                elif data["has_sockets"] == "True" or data["has_sockets"] == "1":
                    data["has_sockets"] = 1

                # Check if field has a boolean value:
                if not (data["has_sockets"] == 0 or data["has_sockets"] == 1):
                    return False, jsonify(result={
                        "validation_error": "Field 'has_sockets' must have a value of either 0, 1, False, or True (and without surrounding quotes)."})

            # FIELD = has_toilet:
            if "has_toilet" in data.keys():
                # Convert string True/False/0/1 to integer equivalents:
                if data["has_toilet"] == "False" or data["has_toilet"] == "0":
                    data["has_toilet"] = 0
                elif data["has_toilet"] == "True" or data["has_toilet"] == "1":
                    data["has_toilet"] = 1

                # Check if field has a boolean value:
                if not (data["has_toilet"] == 0 or data["has_toilet"] == 1):
                    return False, jsonify(result={
                        "validation_error": "Field 'has_toilet' must have a value of either 0, 1, False, or True (and without surrounding quotes)."})

            # FIELD = has_wifi:
            if "has_wifi" in data.keys():
                # Convert string True/False/0/1 to integer equivalents:
                if data["has_wifi"] == "False" or data["has_wifi"] == "0":
                    data["has_wifi"] = 0
                elif data["has_wifi"] == "True" or data["has_wifi"] == "1":
                    data["has_wifi"] = 1

                # Check if field has a boolean value:
                if not (data["has_wifi"] == 0 or data["has_wifi"] == 1):
                    return False, jsonify(result={
                        "validation_error": "Field 'has_wifi' must have a value of either 0, 1, False, or True (and without surrounding quotes)."})

            # FIELD = can_take_calls:
            if "can_take_calls" in data.keys():
                # Convert string True/False/0/1 to integer equivalents:
                if data["can_take_calls"] == "False" or data["can_take_calls"] == "0":
                    data["can_take_calls"] = 0
                elif data["can_take_calls"] == "True" or data["can_take_calls"] == "1":
                    data["can_take_calls"] = 1

                # Check if field has a boolean value:
                if not (data["can_take_calls"] == 0 or data["can_take_calls"] == 1):
                    return False, jsonify(result={
                        "validation_error": "Field 'can_take_calls' must have a value of either 0, 1, False, or True (and without surrounding quotes)."})

            # FIELD = seats:
            if "seats" in data.keys():
                # Check if field is of length <= 250:
                if len(str(data["seats"]).rstrip()) > 250:
                    return False, jsonify(
                        result={"validation_error": "Field 'seats' must have length <= 250 characters."})

            # FIELD = coffee_price:
            if "coffee_price" in data.keys():
                # Check if field is of length <= 250:
                if len(str(data["coffee_price"]).rstrip()) > 250:
                    return False, jsonify(result={
                        "validation_error": "Field 'coffee_price' must have length <= 250 characters."})

            # At this point, validation is deemed to have passed all validation checks.
            # Return successful-validation indication to the calling function
            # (Feedback JSON will not be returned, for final feedback will be deferred to the end
            # of processing the API request in full.):
            return True, ""

        except:
            return False, jsonify(
                result={"validation_error": f"An invalid JSON was provided in the API request."})

    except:  # An error has occurred:
        return False, jsonify(result={"validation_error": "An error has occurred in validating fields for API request."})


def validate_rename_from_api(data):
    """Function to check if all fields in an API "rename cafe" request meet database requirements prior to updating the database"""
    try:
        # Define (via a list) which fields are REQUIRED to be accounted for in the API request:
        required_fields = ["name_old", "name_new"]

        try:
            # COMPARE FIELDS PROVIDED IN THE API REQUEST VS. THOSE THAT ARE EXPECTED BY THE API:
            # Capture which of the required fields have NOT been provided by the API request:
            required_fields_not_provided = [field for field in required_fields if not field in data.keys()]

            # Capture which of the fields provided by the API request are not one of the required fields
            # expected by the API:
            invalid_fields_provided = [field for field in data.keys() if not field in required_fields]

            # Check if at least one required field was not accounted for in the API request.  If so,
            # return validation-failure feedback to the calling function:
            if len(required_fields_not_provided) > 0:
                return False, jsonify(result={
                    "validation_error": f"The following required fields were not provided in the API request: {required_fields_not_provided}."})

            # Check if at least one invalid field was provided in the API request.  If so,
            # return validation-failure feedback to the calling function:
            if len(invalid_fields_provided) > 0:
                return False, jsonify(result={
                    "validation_error": f"The following invalid fields were provided in the API request: {invalid_fields_provided}."})

            # VALIDATE EACH FIELD PROVIDED IN THE API REQUEST:
            # FIELD = name_old:
            # Check if old cafe name exists in the database:
            cafe_name_in_db = retrieve_from_database("get_cafe_by_name", cafe_name=str(data["name_old"]))
            if cafe_name_in_db == {}:
                return False, jsonify(
                    result={"validation_error": "An error has occurred in validating fields for API request."})
            elif cafe_name_in_db == None:
                return False, jsonify(result={
                    "validation_error": f"Cafe name '{data["name_old"]}' does not exist in the database."})
            else:
                # Capture ID tied to old cafe name:
                id_old_cafe_name = cafe_name_in_db.id
                print(id_old_cafe_name)

            # FIELD = name_new:
            # Check if field is of length > 0 and <= 250:
            if len(str(data["name_new"]).rstrip()) == 0 or len(str(data["name_new"]).rstrip()) > 250:
                return False, jsonify(result={
                    "validation_error": "Field 'name_new' must be populated and have length <= 250 characters."})

            # Check if new cafe name does not already exist in the database:
            cafe_name_in_db = retrieve_from_database("get_cafe_by_name", cafe_name=str(data["name_new"]))
            if cafe_name_in_db == {}:
                return False, jsonify(
                    result={"validation_error": "An error has occurred in validating fields for API request."})
            elif cafe_name_in_db != None:
                if cafe_name_in_db.id != id_old_cafe_name:  # Record is not the same as the one targeted for editing.
                    return False, jsonify(result={
                        "validation_error": f"Cafe name '{data["name_new"]}' already exists in the database."})

            # At this point, validation is deemed to have passed all validation checks.
            # Return successful-validation indication to the calling function
            # (Feedback JSON will not be returned, for final feedback will be deferred to the end
            # of processing the API request in full.):
            return True, ""

        except:
            return False, jsonify(
                result={"validation_error": f"An invalid JSON was provided in the API request."})

    except:  # An error has occurred:
        return False, jsonify(result={"validation_error": "An error has occurred in validating fields for API request."})


# Run main function for this application:
run_app()

# Destroy the object that was created to show user dialog and message boxes:
dlg.Destroy()

if __name__ == "__main__":
    app.run(debug=True, port=5003)