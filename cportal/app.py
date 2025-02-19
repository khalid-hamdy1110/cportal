import os
import logging

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import date

from helpers import login_required

logging.getLogger("cs50").disabled = False

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///portal.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def dashboard():
    """Renders the dashboard page"""

    # Getting the user's info from the database
    rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    messages = db.execute("SELECT * FROM messages WHERE reciever = ? ORDER BY id DESC LIMIT 3", rows[0]["username"])

    # If function to show specific versions of dashboard.html according to the role of the user
    if rows[0]['role'] == "admin":

        # Getting the necessary information for the admin's dashboard
        info = db.execute("SELECT * FROM admins WHERE username = ?", rows[0]["username"])
        studentCount = db.execute("SELECT COUNT(*) FROM students")
        teacherCount = db.execute("SELECT COUNT(*) FROM teachers")
        classes = db.execute("SELECT * FROM classes")
        return render_template("dashboard.html", role="a", info=info, studentCount=studentCount, teacherCount=teacherCount, classes=classes, messages=messages)
    elif rows[0]['role'] == "teacher":

        # Getting the necessary information for the teacher's dashboard
        info = db.execute("SELECT * FROM teachers WHERE username = ?", rows[0]["username"])
        classname = db.execute("SELECT * FROM classes WHERE id = (SELECT classid FROM teachers WHERE username = ?)", rows[0]['username'])
        classes = db.execute("SELECT COUNT(*) FROM students WHERE id = (SELECT stdid FROM enrollment WHERE classid = ?)", info[0]['classid'])
        materials = db.execute("SELECT * FROM materials ORDER BY id DESC LIMIT 3")
        assignments = db.execute("SELECT * FROM assignments WHERE className = ? ORDER BY id DESC LIMIT 3", classname[0]['name'])
        enrollment = db.execute("SELECT * FROM enrollment")
        students = db.execute("SELECT * FROM students")
        return render_template("dashboard.html", role="t", info=info, messages=messages, classes=classes, classname=classname, materials=materials, assignments=assignments, enrollment=enrollment, students=students)
    else:

        # Getting the necessary information for the student's dashboard
        info = db.execute("SELECT * FROM students WHERE username = ?", rows[0]["username"])
        enrollment = db.execute("SELECT * FROM enrollment WHERE stdid = (SELECT id FROM students WHERE username = ?)", rows[0]['username'])
        
        # Getting the class names that the student is enrolled in
        classnames = []
        for i in range(len(enrollment)):
            classtemp = db.execute("SELECT * FROM classes WHERE id = ?", enrollment[i]['classid'])
            classnames.append(classtemp[0])

        # Getting the assignments that belongs to student
        assignments = []
        for i in range(len(classnames)):
            assignmenttemp = db.execute("SELECT * FROM assignments WHERE className = ?", classnames[i]['name'])
            for j in range(len(assignmenttemp)):
                assignments.append(assignmenttemp[j])

        # Getting the users submissions then storing the assignments that haven't been submitted
        submissions = db.execute("SELECT * FROM submissions WHERE stdid = ?", info[0]['id'])
        assignmentsnotdone = []
        assignmentsdoneid = []
        if submissions:
            for i in range(len(assignments)):
                for j in range(len(submissions)):
                    if submissions[j]['assignmentid'] == assignments[i]['id']:
                        assignmentsdoneid.append(assignments[i]['id'])
            for i in range(len(assignments)):
                if assignments[i]['id'] not in assignmentsdoneid:
                    assignmentsnotdone.append(assignments[i])
        else:
            for j in range(len(assignments)):
                assignmentsnotdone.append(assignments[j])
        assignmentMarks = db.execute("SELECT * FROM assignment_marks WHERE stdid = ?", info[0]['id'])
        return render_template("dashboard.html", role="s", info=info, messages=messages, assignments=assignments, assignmentsnotdone=assignmentsnotdone, assignmentMarks=assignmentMarks, classnames=classnames)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash('Must provide username!')
            return redirect("/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash('Must provide password!')
            return redirect("/login")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash('Invalid username and/or password!')
            return redirect("/login")
        
        # Forget any user_id
        session.clear()

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        db.execute("INSERT INTO login_history(login_date, IP, username) VALUES(?, ?, ?)", date.today(), request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr), request.form.get("username"))

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/materials")
@login_required
def materials():
    """Renders the materials page"""

    # Getting the user's info from the databasee
    rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    materials = db.execute("SELECT * FROM materials ORDER BY filename")

    # If function to show specific versions of materials.html according to the role of the user
    if rows[0]['role'] == "admin":
        info = db.execute("SELECT * FROM admins WHERE username = ?", rows[0]["username"])
        classes = db.execute("SELECT * FROM classes")
        return render_template("materials.html", role="a", info=info, classes=classes, materials=materials)
    elif rows[0]['role'] == "teacher":
        info = db.execute("SELECT * FROM teachers WHERE username = ?", rows[0]["username"])
        classes = db.execute("SELECT * FROM classes WHERE id = (SELECT classid FROM teachers)")

        # If there are no classes a message is rendered that there is no classes
        if not classes:
            return render_template("noclasses.html", role="t")
        return render_template("materials.html", role="t", info=info, classes=classes, materials=materials)
    else:
        info = db.execute("SELECT * FROM students WHERE username = ?", rows[0]["username"])
        enrollment = db.execute("SELECT * FROM enrollment WHERE stdid = (SELECT id FROM students WHERE username = ?)", rows[0]["username"])
        
        # Getting the classes that the student is enrolled in
        classes = []
        for i in range(len(enrollment)):
            if i > 0:
                classes2 = db.execute("SELECT * FROM classes WHERE id = ?", enrollment[i]["classid"])
                if classes2:
                    classes.append(classes2[0])
            else:
                classes = db.execute("SELECT * FROM classes WHERE id = ?", enrollment[i]["classid"])
        
        # If there are no classes a message is rendered that there is no classes
        if not classes:
            return render_template("noclasses.html", role="s")
        return render_template("materials.html", role="s", info=info, classes=classes, materials=materials)


@app.route("/assignments")
@login_required
def assignments():
    """Renders the assignments page"""

    # Getting the user's info from the database
    rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    assignments = db.execute("SELECT * FROM assignments ORDER BY name")
    marks = db.execute("SELECT * FROM assignment_marks WHERE stdid = (SELECT id FROM students WHERE username = (SELECT username FROM users WHERE id = ?))", session["user_id"])
    submissions = db.execute("SELECT * FROM submissions WHERE stdid = (SELECT id FROM students WHERE username = (SELECT username FROM users WHERE id = ?))", session["user_id"])
    attatchments = db.execute("SELECT * FROM attatchments ORDER BY filename")

    # If function to show specific versions of assignments.html according to the role of the user
    if rows[0]['role'] == "admin":
        info = db.execute("SELECT * FROM admins WHERE username = ?", rows[0]["username"])
        classes = db.execute("SELECT * FROM classes")
        return render_template("assignments.html", role="a", info=info, classes=classes, assignments=assignments, attatchments=attatchments, today=date.today(), submissions=submissions, marks=marks)
    elif rows[0]['role'] == "teacher":
        info = db.execute("SELECT * FROM teachers WHERE username = ?", rows[0]["username"])
        classes = db.execute("SELECT * FROM classes WHERE id = (SELECT classid FROM teachers)")

        # If there are no classes a message is rendered that there is no classes
        if not classes:
            return render_template("noclasses.html", role="t")
        return render_template("assignments.html", role="t", info=info, classes=classes, assignments=assignments, attatchments=attatchments, today=date.today(), submissions=submissions, marks=marks)
    else:
        info = db.execute("SELECT * FROM students WHERE username = ?", rows[0]["username"])
        enrollment = db.execute("SELECT * FROM enrollment WHERE stdid = (SELECT id FROM students WHERE username = ?)", rows[0]["username"])
        
        # Getting the classes that the student is enrolled in
        classes = []
        for i in range(len(enrollment)):
            if i > 0:
                classes2 = db.execute("SELECT * FROM classes WHERE id = ?", enrollment[i]["classid"])
                if classes2:
                    classes.append(classes2[0])
            else:
                classes = db.execute("SELECT * FROM classes WHERE id = ?", enrollment[i]["classid"])

        # If there are no classes a message is rendered that there is no classes
        if not classes:
            return render_template("noclasses.html", role="s")
        return render_template("assignments.html", role="s", info=info, classes=classes, assignments=assignments, attatchments=attatchments, today=date.today(), submissions=submissions, marks=marks)


@app.route("/databaseS", methods=["GET", "POST"])
@login_required
def databaseS():
    """Renders the student database"""

    if request.method == "POST":

        # Getting the form info
        stdid = db.execute("SELECT id FROM students ORDER BY id DESC LIMIT 1")
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        username = request.form.get("username")
        gender = request.form.get("gender")
        email = request.form.get("email")
        phone = request.form.get("phone")
        DOB = request.form.get("DOB")
        password = request.form.get("pass")
        usernameCheck = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Validating that there are no missing fields
        if not fname or not lname or not username or not gender or not email or not phone or not DOB or not password:
            flash("Missing Fields!")
            return redirect("/databaseS")

        # Making sure that the username entered isn't already present
        if usernameCheck:
            flash("Username already present!")
            return redirect("/databaseS")
        
        # If there is no stdid the id is set as 1 otherwise it is incremented
        if not stdid:
             
            # Inserting the data from the fields into the database
            db.execute("INSERT INTO students(id, First_Name, Last_Name, username, gender, email, phone, DOB) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                    1, fname, lname, username, gender, email, phone, DOB)

            # Inserting a new user into the user's database
            db.execute("INSERT INTO users(role, username, hash) VALUES(?, ?, ?)", "student", username, generate_password_hash(password))
        else:

            # Inserting the data from the fields into the database
            db.execute("INSERT INTO students(id, First_Name, Last_Name, username, gender, email, phone, DOB) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                    (stdid[0]["id"] + 1), fname, lname, username, gender, email, phone, DOB)

            # Inserting a new user into the user's database
            db.execute("INSERT INTO users(role, username, hash) VALUES(?, ?, ?)", "student", username, generate_password_hash(password))

        return redirect("/databaseS")
    else:
        # Getting the user's info from the database
        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # If function to show specific versions of databaseS.html according to the role of the user
        if rows[0]['role'] == "admin":
            
            # Getting the search keywords and how it will be searched
            search = request.args.get("search")
            by = request.args.get("by")

            # If there is a search the students variable is adjusted to display the filtered data
            if search:
                if by == 'id':
                    students = db.execute("SELECT * FROM students WHERE id LIKE ?", search)
                elif by == 'username':
                    students = db.execute("SELECT * FROM students WHERE username LIKE ?", search)
                elif by == 'name':
                    search = search.split()
                    if len(search) == 1:
                        students = db.execute("SELECT * FROM students WHERE First_Name LIKE ?", search[0])
                    else:
                        students = db.execute("SELECT * FROM students WHERE First_Name LIKE ? AND Last_Name LIKE ?", search[0], search[1])
                else:
                    students = db.execute("SELECT * FROM students")
            else:
                students = db.execute("SELECT * FROM students")
            classes = db.execute("SELECT * FROM classes")
            enrollment = db.execute("SELECT * FROM enrollment")
            return render_template("databaseS.html", role="a", students=students, classes=classes, enrollment=enrollment)
        else:
            return redirect("/")


@app.route("/databaseT", methods=["GET", "POST"])
@login_required
def databaseT():
    """Rendering the teachers database"""

    if request.method == "POST":

        # Getting the form data
        tchid = db.execute("SELECT id FROM teachers ORDER BY id DESC LIMIT 1")
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        username = request.form.get("username")
        classid = request.form.get("classid")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("pass")
        usernameCheck = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Making sure there are no missing fields
        if not fname or not lname or not username or not classid or not email or not phone or not password:
            flash("Missing Fields!")
            return redirect("/databaseT")

        # Making sure the classid entered is valid
        if not db.execute("SELECT * FROM classes WHERE id = ?", classid):
            flash("Not a valid Class ID!")
            return redirect("/databaseT")

        # Making sure the username entered isn't already present in the database
        if usernameCheck:
            flash("Username already present!")
            return redirect("/databaseT")

        # If there is no tchid the id is set as 1 otherwise it is incremented
        if not tchid:
            
            # Inserting the data from the fields into the database
            db.execute("INSERT INTO teachers(id, First_Name, Last_Name, username, classid, email, phone) VALUES(?, ?, ?, ?, ?, ?, ?)", 1,
                    fname, lname, username, classid, email, phone)
            
            # Inserting a new user into the user's database
            db.execute("INSERT INTO users(role, username, hash) VALUES(?, ?, ?)", "teacher", username, generate_password_hash(password))
        else:

            # Inserting the data from the fields into the database
            db.execute("INSERT INTO teachers(id, First_Name, Last_Name, username, classid, email, phone) VALUES(?, ?, ?, ?, ?, ?, ?)",
                    (tchid[0]["id"] + 1), fname, lname, username, classid, email, phone)

            # Inserting a new user into the user's database
            db.execute("INSERT INTO users(role, username, hash) VALUES(?, ?, ?)", "teacher", username, generate_password_hash(password))

        return redirect("/databaseT")
    else:
        # Getting the user's info from the database
        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # If function to show specific versions of databaseT.html according to the role of the user
        if rows[0]['role'] == "admin":

            # Getting the search keywords and how it will be searched
            search = request.args.get("search")
            by = request.args.get("by")

            # If there is a search the students variable is adjusted to display the filtered data
            if search:
                if by == 'id':
                    teachers = db.execute("SELECT * FROM teachers WHERE id LIKE ?", search)
                elif by == 'username':
                    teachers = db.execute("SELECT * FROM teachers WHERE username LIKE ?", search)
                elif by == 'name':
                    search = search.split()
                    if len(search) == 1:
                        teachers = db.execute("SELECT * FROM teachers WHERE First_Name LIKE ?", search[0])
                    else:
                        teachers = db.execute("SELECT * FROM teachers WHERE First_Name LIKE ? AND Last_Name LIKE ?", search[0], search[1])
                else:
                    teachers = db.execute("SELECT * FROM teachers")
            else:
                teachers = db.execute("SELECT * FROM teachers")
            return render_template("databaseT.html", role="a", teachers=teachers)
        else:
            return redirect("/")


@app.route("/delete", methods=["POST"])
@login_required
def delete():
    """Delete a student/teacher from the database"""

    if request.method == "POST":
        
        # Getting form data
        info = request.form.get("delete")
        info = info.split()
        
        # If the info gotten from the form an issue is raised
        if len(info) != 3:
            flash("Issue Occured!")
            return redirect("/")

        # Deleting from the database the user
        if info[0] == 'students':
            db.execute("DELETE FROM enrollment WHERE stdid = (SELECT id FROM students WHERE username = ?)", info[1])
        db.execute("DELETE FROM ? WHERE username = ?", info[0], info[1])
        db.execute("DELETE FROM users WHERE username = ?", info[1])
        return redirect(f"/{info[2]}")
    else:
        return redirect("/")


@app.route("/uploader", methods=["POST"])
@login_required
def upload_file():
    """Uploads a file to the materials page"""

    if request.method == "POST":

        # Getting the file uploaded from the form
        f = request.files['file']

        # Making sure there is a file and form data is there
        if not f or not request.form.get("classname"):
            flash("Missing file/field!")
            return redirect("/materials")

        # Declaring a secure filename
        filename = secure_filename(f.filename)
        f.save(os.path.join("./material_uploads", filename))
        db.execute("INSERT INTO materials(filename, classname) VALUES(?, ?)", filename, request.form.get("classname"))
        return redirect("/materials")
    else:
        return redirect("/")


@app.route("/downloader", methods=["GET", "POST"])
@login_required
def download_file():
    """Downloading a material file"""

    if request.method == "POST":

        # Making sure form data is present
        if not request.form.get("filename"):
            flash("Missing filename!")
            return redirect("/materials")
        filename = db.execute("SELECT * FROM materials WHERE filename = ?", request.form.get("filename"))
        return send_file(os.path.join("./material_uploads", filename[0]["filename"]), as_attachment=True)
    else:
        return redirect("/")


@app.route("/deleter", methods=["GET", "POST"])
@login_required
def deleter():
    """Deleting files from materials"""

    if request.method == "POST":

        # Making sure that form data is present
        if not request.form.get("filename"):
            flash("Missing filename!")
            return redirect("/materials")

        # Deleting the file from database and from the material_uploads file
        db.execute("DELETE FROM materials WHERE filename = ?", request.form.get("filename"))
        os.remove(os.path.join("./material_uploads", request.form.get("filename")))
        return redirect("/materials")
    else:
        return redirect("/")


@app.route("/assignment-maker", methods=["GET", "POST"])
@login_required
def assignment_maker():
    """Makes an assignment"""

    if request.method == "POST":

        # Getting the form data
        f = request.files['file']
        info = request.form.get("info")
        info = info.split()

        # Making that there are no missing fields
        if not request.form.get("name") or not request.form.get("description") or not request.form.get("totalmarks") or not request.form.get("duedate"):
            flash("Missing Fields!")
            return redirect("/assignments")

        # If there is a file a file is inserted into the attachments folder and database otherwise only an assignment is made
        if f:

            # Making sure that filename is secure
            filename = secure_filename(f.filename)
            f.save(os.path.join("./attatchments", filename))

            # Inserting the filename and other form data into the assignments and attatchments database
            db.execute("INSERT INTO assignments(name, description, className, totalMarks, creationDate, dueDate) VALUES(?, ?, ?, ?, ?, ?)",
                        request.form.get("name"), request.form.get("description"), info[0], request.form.get("totalmarks"),
                        date.today(), request.form.get("duedate"))
            typeid = db.execute("SELECT id FROM assignments ORDER BY id DESC LIMIT 1")
            db.execute("INSERT INTO attatchments(filename, type, typeid) VALUES(?, ?, ?)", filename, info[1], typeid[0]['id'])
        else:
            
            # Inserting the form data into the assignments database
            db.execute("INSERT INTO assignments(name, description, className, totalMarks, creationDate, dueDate) VALUES(?, ?, ?, ?, ?, ?)",
                        request.form.get("name"), request.form.get("description"), info[0], request.form.get("totalmarks"),
                        date.today(), request.form.get("duedate"))
        return redirect("/assignments")
    else:
        return redirect("/")


@app.route("/assignment-remover", methods=["GET", "POST"])
@login_required
def assignment_remover():
    """Removing an assignment"""

    if request.method == "POST":

        # Getting form data
        assignmentid = request.form.get("assignmentDelete")
        
        # Making sure there are no missing form data
        if not assignmentid:
            flash("Missing Fields!")
            return redirect("/assignments")
        attatchments = db.execute("SELECT * FROM attatchments WHERE type = 'assignment' AND typeid = ?", assignmentid)
        submissions = db.execute("SELECT * FROM submissions WHERE assignmentid = ?", assignmentid)
        assignmentmarks = db.execute("SELECT * FROM assignment_marks WHERE assignmentid = ?", assignmentid)

        # Deleting the assignment from the assignments database
        db.execute("DELETE FROM assignments WHERE id = ?", assignmentid)
        
        # If there are attatchments they are deleted
        if attatchments:
            db.execute("DELETE FROM attatchments WHERE type = 'assignment' AND typeid = ?", assignmentid)
        
        # If there are any submissions to that assignment, they are deleted
        if submissions:
            for i in range(len(submissions)):
                subattatchments = db.execute("SELECT * FROM attatchments WHERE type = 'submission' AND typeid = ?", submissions[i]['id'])
                db.execute("DELETE FROM attatchments WHERE type = 'submission' AND typeid = ?", submissions[i]['id'])
                os.remove(os.path.join("./attatchments", subattatchments[i]['filename']))
            db.execute("DELETE FROM submissions WHERE assignmentid = ?", assignmentid)
        
        # If any of the submissions have been marked then they are deleted from the database
        if assignmentmarks:
            db.execute("DELETE FROM assignment_marks WHERE assignmentid = ?", assignmentid)

        return redirect("/assignments")
    else:
        return redirect("/")


@app.route("/attatchment-uploader", methods=["GET", "POST"])
@login_required
def attatchment_upload():
    """Uploading attatchments that belong to submissions or assignments"""

    if request.method == "POST":

        # Getting form data and file
        f = request.files['file']
        type = request.form.get("type")
        type = type.split()

        # Making sure that the file and form data is present
        if len(type) != 3 or not f:
            flash("Missing Fields/Files!")
            return redirect("/assignments")
        
        # If the type is submission it is added to the attatchments table and submissions table
        # Otherwise it is added to the attatchments table as an assignment
        if type[0] == 'submission':
            stdid = db.execute("SELECT id FROM students WHERE username = (SELECT username FROM users WHERE id = ?)", session["user_id"])
            onTime = "Yes"
            today = date.today()
            dueDate = type[2].split("-")

            # Checks if the submission is on time
            if today > date(int(dueDate[0]), int(dueDate[1]), int(dueDate[2])):
                onTime = "No"
            
            # Inserting into the submissions table
            db.execute("INSERT INTO submissions(stdid, assignmentid, onTime, submissionDate) VALUES(?, ?, ?, ?)", stdid[0]["id"], type[1], onTime, today)
            typeid = db.execute("SELECT id FROM submissions WHERE stdid = ? AND assignmentid = ?", stdid[0]["id"], type[1])
            filename = secure_filename(f.filename)
            f.save(os.path.join("./attatchments", filename))
            db.execute("INSERT INTO attatchments(filename, typeid, type) VALUES(?, ?, ?)", filename, typeid[0]["id"], type[0])
        else:
            filename = secure_filename(f.filename)
            f.save(os.path.join("./attatchments", filename))
            db.execute("INSERT INTO attatchments(filename, typeid, type) VALUES(?, ?, ?)", filename, type[1], type[0])
        return redirect("/assignments")
    else:
        return redirect("/")


@app.route("/attatchment-downloader", methods=["GET", "POST"])
@login_required
def attatchment_download():
    """Downloads Attatchments"""
    
    if request.method == "POST":

        # Getting form data
        fileinfo = request.form.get("fileinfo")
        fileinfo = fileinfo.split()
        
        # Making sure there is no missing form data
        if len(fileinfo) != 3:
            flash("Missing Fields!")
            return redirect("/")
        
        # Sends the download of the file
        filename = db.execute("SELECT * FROM attatchments WHERE filename = ? AND typeid = ? AND type = ?", fileinfo[0], fileinfo[1], fileinfo[2])
        return send_file(os.path.join("./attatchments", filename[0]["filename"]), as_attachment=True)
    else:
        return redirect("/")

@app.route("/submissions")
@login_required
def submissions():
    """Renders the submissions page"""
    
    # Getting user's info from the database
    rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    assignments = db.execute("SELECT * FROM assignments ORDER BY name")
    submissions = db.execute("SELECT * FROM submissions")
    students = db.execute("SELECT * FROM students")
    attatchments = db.execute("SELECT * FROM attatchments WHERE type = 'submission'")
    marks = db.execute("SELECT * FROM assignment_marks")

    # If function to show specific versions of submissions.html according to the role of the user
    if rows[0]['role'] == "admin":
        classes = db.execute("SELECT * FROM classes")
        return render_template("submissions.html", role="a", classes=classes, assignments=assignments, submissions=submissions, students=students, attatchments=attatchments, marks=marks)
    elif rows[0]['role'] == "teacher":
        classes = db.execute("SELECT * FROM classes WHERE id = (SELECT classid FROM teachers)")
        
        # If there are no classes then it renders the noclasses.html
        if not classes:
            return render_template("noclasses.html", role="t")
        return render_template("submissions.html", role="t", classes=classes, assignments=assignments, submissions=submissions, students=students, attatchments=attatchments, marks=marks)
    else:
        return redirect("/assignments")


@app.route("/marker", methods=["GET", "POST"])
@login_required
def marker():
    """Marking a student's assignment"""

    if request.method == "POST":

        # Getting form data
        marks = request.form.get("marks")
        marks = marks.split()

        # Making sure all form data is present
        if len(marks) != 4 or not request.form.get("mark") or not request.form.get("comment"):
            flash("Missing Fields!")
            return redirect("/submissions")
        
        # Inserting form data into the assignment_marks table
        db.execute("INSERT INTO assignment_marks(assignmentid, stdid, marks, totalMarks, comment, submissionid) VALUES(?, ?, ?, ?, ?, ?)", marks[0], marks[1], request.form.get("mark"), marks[2], request.form.get("comment"), marks[3])
        return redirect("/submissions")
    else:
        return redirect("/")


@app.route("/enrollment", methods=["GET", "POST"])
@login_required
def enrollment():
    """Enrolling a student into subjects"""
    
    if request.method == "POST":

        # Getting form data
        stdid = request.form.get("stdid")
        selected = request.form.getlist("classes")

        # Making sure form data is present
        if not stdid or not selected:
            flash("Missing Fields!")
            return redirect("/databaseS")
        
        # Inserting all subjects selected into the database
        for i in range(len(selected)):
            if selected:
                db.execute("INSERT INTO enrollment(stdid, classid) VALUES(?, ?)", stdid, selected[i])
        return redirect('/databaseS')
    else:
        return redirect("/")


@app.route("/unenrollment", methods=["GET", "POST"])
@login_required
def unenrollment():
    """Unenrolling students from subjects"""
    
    if request.method == "POST":

        # Getting form data
        stdid = request.form.get("stdid")
        selected = request.form.getlist("classes")

        # Making sure form data is present
        if not stdid or not selected:
            flash("Missing Fields!")
            return redirect("/databaseS")

        # Deleting selected enrolled subjects from the enrollment table 
        for i in range(len(selected)):
            if selected:
                db.execute("DELETE FROM enrollment WHERE stdid = ? AND classid = ?", stdid, selected[i])
        return redirect('/databaseS')
    else:
        return redirect("/")


@app.route("/settings")
@login_required
def settings():
    """Rendering the settings page"""

    # Getting the user's info from the database
    rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    loginHistory = db.execute("SELECT * FROM login_history WHERE username = (SELECT username FROM users WHERE id = ?)", session['user_id'])

    # If function to show specific versions of settings.html according to the role of the user
    if rows[0]['role'] == "admin":
        info = db.execute("SELECT * FROM admins WHERE username = ?", rows[0]["username"])
        return render_template("settings.html", role="a", info=info, loginHistory=loginHistory)
    elif rows[0]['role'] == "teacher":
        info = db.execute("SELECT * FROM teachers WHERE username = ?", rows[0]["username"])
        return render_template("settings.html", role="t", info=info, loginHistory=loginHistory)
    else:
        info = db.execute("SELECT * FROM students WHERE username = ?", rows[0]["username"])
        return render_template("settings.html", role="s", info=info, loginHistory=loginHistory)


@app.route("/change-pass", methods=["GET", "POST"])
@login_required
def changepassword():
    """Changing a user's password"""

    if request.method == "POST":
        
        # Getting the user's password
        hash = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Making sure that all form data is present 
        if not request.form.get("currentPass") or not request.form.get("newPass") or not request.form.get("confirmPass"):
            flash("Missing Fields")
            return redirect("/settings")
        
        # Checking if password and entered password are the same
        elif not check_password_hash(hash[0]["hash"], request.form.get("currentPass")):
            flash("Wrong Current Password")
            return redirect("/settings")
        
        # Checking if the new password is the same as the confirmation
        elif request.form.get("newPass") != request.form.get("confirmPass"):
            flash("Wrong Password Confirmation")
            return redirect("/settings")

        # Updates the users password
        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(request.form.get("newPass")), session['user_id'])

        return redirect("/settings")
    else:
        return redirect("/")


@app.route("/change-contact", methods=["GET", "POST"])
@login_required
def changecontact():
    """Change's the user's contact info"""

    if request.method == "POST":

        # Getting form data
        change = request.form.get("change")
        change = change.split()

        # Making sure that there are no missing fields
        if len(change) != 3 or not request.form.get("email") or not request.form.get("phone"):
            flash("Missing Fields!")
            return redirect("/settings")
        
        # Checking which role to access the correct table and change the email or phone according to what is being changed
        if change[0] == "a":
            if change[1] == "email":
                db.execute("UPDATE admins SET email = ? WHERE id = ?", request.form.get("email"), change[2])
            elif change[1] == "phone":
                db.execute("UPDATE admins SET phone = ? WHERE id = ?", request.form.get("phone"), change[2])
        if change[0] == "t":
            if change[1] == "email":
                db.execute("UPDATE teachers SET email = ? WHERE id = ?", request.form.get("email"), change[2])
            elif change[1] == "phone":
                db.execute("UPDATE teachers SET phone = ? WHERE id = ?", request.form.get("phone"), change[2])
        else:
            if change[1] == "email":
                db.execute("UPDATE students SET email = ? WHERE id = ?", request.form.get("email"), change[2])
            elif change[1] == "phone":
                db.execute("UPDATE students SET phone = ? WHERE id = ?", request.form.get("phone"), change[2])
        return redirect("/settings")
    else:
        return redirect("/")


@app.route("/messages")
@login_required
def messages():
    """Renders the messages page"""

    # Getting the user's data from the database
    rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

    # If the user chose to filter the sent messages the messages variable is adjusted accordingly
    if request.args.get("filter") == "sent":
        messages = db.execute("SELECT * FROM messages WHERE sender = ? ORDER BY id DESC", rows[0]["username"])
    else:
        messages = db.execute("SELECT * FROM messages WHERE reciever = ? ORDER BY id DESC", rows[0]["username"])

    # If function to show specific versions of messages.html according to the role of the user
    if rows[0]['role'] == "admin":
        info = db.execute("SELECT * FROM admins WHERE username = ?", rows[0]["username"])
        return render_template("messages.html", role="a", info=info, messages=messages, message=request.args.get("filter"))
    elif rows[0]['role'] == "teacher":
        info = db.execute("SELECT * FROM teachers WHERE username = ?", rows[0]["username"])
        return render_template("messages.html", role="t", info=info, messages=messages, message=request.args.get("filter"))
    else:
        info = db.execute("SELECT * FROM students WHERE username = ?", rows[0]["username"])
        return render_template("messages.html", role="s", info=info, messages=messages, message=request.args.get("filter"))


@app.route("/send", methods=["GET", "POST"])
@login_required
def sendmessage():
    """Sending a message"""

    if request.method == "POST":
        role = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        to = request.form.get("to")

        # Checking if the role is student to restrict who can be messaged
        if role[0]['role'] == 'student':
            enrollment = db.execute("SELECT * FROM enrollment WHERE stdid = (SELECT id FROM students WHERE username = ?)", role[0]['username'])
            teachers = db.execute("SELECT * FROM teachers")

            # Getting who the student is allowed to message which is the student's teachers
            allowedContacts = []
            for i in range(len(enrollment)):
                for j in range(len(teachers)):
                    if enrollment[i]['classid'] == teachers[j]['classid']:
                        allowedContacts.append(teachers[j]['username'])
            
            # Checking if the student can message the recepient 
            if not allowedContacts or to not in allowedContacts:
                flash("You don't have permission to contact that person!")
                return redirect("/messages")

        # Getting form data
        subject = request.form.get("subject")
        description = request.form.get("description")

        # Checking that form data is present
        if not to or not subject or not description or not to:
            flash("Missing Fields!")
            return redirect("/messages")

        # Getting the user's username
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        db.execute("INSERT INTO messages(subject, description, reciever, sender, creationDate) VALUES(?, ?, ?, ?, ?)", subject, description, to, username[0]['username'], date.today())
        return redirect("/messages")
    else:
        return redirect("/messages")


@app.route("/sendGroupMessage", methods=["GET", "POST"])
@login_required
def sendGroupMessage():
    """Sending a group message"""

    if request.method == "POST":
        
        # Getting form data
        subject = request.form.get("subject")
        description = request.form.get("description")
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        to = request.form.get("to")

        # Making sure that form data is present
        if not to or not subject or not description:
            flash("Missing Fields!")
            return redirect("/messages")

        # If function to check who to send the message to and to send it to everyone in that group
        if to == "admins":
            admins = db.execute("SELECT * FROM users WHERE role = 'admin'")
            for i in range(len(admins)):
                db.execute("INSERT INTO messages(subject, description, reciever, sender, creationDate) VALUES(?, ?, ?, ?, ?)", subject, description, admins[i]['username'], username[0]['username'], date.today())
        elif to == "teachers":
            teachers = db.execute("SELECT * FROM users WHERE role = 'teacher'")
            for i in range(len(teachers)):
                db.execute("INSERT INTO messages(subject, description, reciever, sender, creationDate) VALUES(?, ?, ?, ?, ?)", subject, description, teachers[i]['username'], username[0]['username'], date.today())
        elif to == "students":
            students = db.execute("SELECT * FROM users WHERE role = 'student'")
            for i in range(len(students)):
                db.execute("INSERT INTO messages(subject, description, reciever, sender, creationDate) VALUES(?, ?, ?, ?, ?)", subject, description, students[i]['username'], username[0]['username'], date.today())
        return redirect("/messages")
    else:
        return redirect("/")


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')