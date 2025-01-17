import datetime
from dotenv import load_dotenv
from flask import Flask, flash, render_template, redirect, url_for, request, session, send_file
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")

# MongoDB Configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# Index Route, Login Page
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("login.html")  

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if mongo.db.users.find_one({"email": email}):
            return render_template("register.html", error="Email already exists! Try logging in.")

        mongo.db.users.insert_one({"name": name, "email": email, "password": password})
        return redirect(url_for("login"))

    return render_template("register.html")  

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = mongo.db.users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            return redirect(url_for("home"))

        # Render the login page with an error message
        return render_template("login.html", error="Invalid credentials! Please try again.")
    
    # Render login page without any error for GET request
    return render_template("login.html")


# Logout Route
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

# Home Route
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("index"))
    return render_template("home.html")  

# Steps to Fill the Details
# Name and About form
@app.route("/step1", methods=["GET", "POST"])
def step1():
    if "user_id" not in session:
        return redirect (url_for("index"))

    if request.method == "POST":
        name = request.form["name"]
        about = request.form["about"]
        skills = request.form.getlist("skills")
        skills = [skill.strip() for skill in skills if skill.strip()]

        mongo.db.profiles.update_one(
            {"user_id": session["user_id"]},
            {"$set": {"name": name, "about": about, "skills": skills}},
            upsert=True
        )
        return redirect(url_for("step2"))

    profile = mongo.db.profiles.find_one({"user_id": session["user_id"]}) or {}
    return render_template("step1.html", profile=profile)  

# Contact Info form
@app.route("/step2", methods=["GET", "POST"])
def step2():
    if "user_id" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        contact_info = {
            "phone": request.form["phone"],
            "email": request.form["email"],
            "linkedin": request.form["linkedin"],
            "github": request.form["github"]
        }

        mongo.db.profiles.update_one(
            {"user_id": session["user_id"]},
            {"$set": {"contact_info": contact_info}},
            upsert=True
        )
        return redirect(url_for("step3"))

    profile = mongo.db.profiles.find_one({"user_id": session["user_id"]}) or {}
    return render_template("step2.html", profile=profile)  

 # Education form
@app.route("/step3", methods=["GET", "POST"])
def step3():
    if "user_id" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        education = {
            "course": request.form["course"],
            "college": request.form["college"],
            "year": request.form["year"]
        }

        mongo.db.profiles.update_one(
            {"user_id": session["user_id"]},
            {"$set": {"education": education}},
            upsert=True
        )
        return redirect(url_for("step4"))

    profile = mongo.db.profiles.find_one({"user_id": session["user_id"]}) or {}
    return render_template("step3.html", profile=profile) 

 # Projects form
@app.route("/step4", methods=["GET", "POST"])
def step4():
    if "user_id" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        projects = []
        project_index = 1
        while True:
            title = request.form.get(f"project_title_{project_index}")
            description = request.form.get(f"project_description_{project_index}")
            link = request.form.get(f"project_link_{project_index}")

            if not title and not description and not link:
                break

            projects.append({"title": title, "description": description, "link": link})
            project_index += 1

        mongo.db.profiles.update_one(
            {"user_id": session["user_id"]},
            {"$set": {"projects": projects}},
            upsert=True
        )
        return redirect(url_for("step5"))

    profile = mongo.db.profiles.find_one({"user_id": session["user_id"]}) or {}
    return render_template("step4.html", profile=profile) 

# Select Theme
@app.route("/step5", methods=["GET", "POST"])
def step5():
    if "user_id" not in session:
        return redirect(url_for("index"))

    theme_folder = os.path.join(app.root_path, "templates/theme")  # Path to the themes folder
    themes = [f for f in os.listdir(theme_folder) if f.endswith(".html")]  # Get all HTML files

    if request.method == "POST":
        theme = request.form.get("theme")  # Get selected theme

        # Update theme in the database
        mongo.db.profiles.update_one(
            {"user_id": session["user_id"]},
            {"$set": {"theme": theme}},
            upsert=True
        )

        return redirect(url_for("preview"))

    return render_template("step5.html", themes=themes) 

# Resume Route
@app.route("/view_profile")
def view_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))  # Redirect to login if not logged in

    # Fetch the profile details from MongoDB
    profile = mongo.db.profiles.find_one({"user_id": session["user_id"]})
    if not profile:
        return "Profile not found! Please set up your profile."

    return render_template("view_profile.html", profile=profile)

# Cooking the website
@app.route("/preview")
def preview():
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    profile = mongo.db.profiles.find_one({"user_id": session["user_id"]})
    if not profile:
        return redirect(url_for("step1"))  # Redirect to step 1 if profile doesn't exist

    # Dynamically load the selected theme
    theme = profile.get("theme", "Cybersecurity Theme.html") 
    theme_path = f"theme/{theme}"  # Include the 'theme/' folder in the path

    return render_template(theme_path, profile=profile)  # Render the selected theme

# About Page
@app.route("/about")
def about():
    if "user_id" not in session:
        return redirect(url_for("index"))
    return render_template("about.html")

# Contact Us
@app.route("/contact", methods=['GET', 'POST'])
def contact():
    # Ensure user is logged in
    if "user_id" not in session:
        flash("You need to log in to access the contact page.", "error")
        return redirect(url_for("index"))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if not name or not email or not message:
            flash("All fields are required!", "error")
            return redirect(url_for("contact"))
        
        try:
            # Insert the data into the database
            mongo.db.messages.insert_one({
                'name': name,
                'email': email,
                'message': message,
                'timestamp': datetime.datetime.utcnow()
            })
            flash('Message sent successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')
        
        return redirect(url_for('contact'))
    
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True)
