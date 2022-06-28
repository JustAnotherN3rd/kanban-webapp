from importlib import import_module
import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, apology



app = Flask(__name__)


app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///kanban.db")

# set current mission to NULL
current_mission = {}


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("name"):
            return apology("Provide Username!")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Provide Password!")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE name = ?", request.form.get("name"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("Invlaid Password!")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["POST","GET"])
def register():

    if request.method == "POST":

        # check for input
        if not request.form.get("name"):
            return apology("Provide Username!")

        rows = db.execute("SELECT * FROM users WHERE name = ?", name)

        # check if name is already used or not so alll names are unique
        if rows[0] != None:
            return apology("Name already taken!")
        
        if not request.form.get("password"):
            return apology("Provide Password!")

        if not request.form.get("confirmation"):
            return apology("Cofirm Password!")
        
        # set vars so it can be inserted into db
        name = request.form.get("name")
        password = request.form.get("password")

        # check for confirmation match with password
        if not password == request.form.get("confirmation"):
            return apology("Confirmation of Password incorrect!")

        # hash password and insert the stuff into the db->users
        hash = generate_password_hash(password)

        db.execute("INSERT INTO users(name,password) VALUES (?,?)", name, hash)

        # go to login to start new sesssion
        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/")
@login_required
def index():

    # get all the tasks in the backlog
    backlog = db.execute("SELECT * FROM tasks WHERE state = 1 AND user_id = ?", session["user_id"])

    # get all tasks inprogress
    inProg = db.execute("SELECT * FROM tasks WHERE state = 2 AND user_id = ?", session["user_id"])

    # get alldone tasks
    done = db.execute("SELECT * FROM tasks WHERE state = 3 AND user_id = ?", session["user_id"])

    return render_template("index.html",backlog=backlog, inProg=inProg, done=done)


@app.route("/new_task", methods=["POST", "GET"])
@login_required
def new_task():
    if request.method == "POST":
        if not request.form.get("name"):
            return apology("Provide Name for the task!")

        name = request.form.get("name")
        desc = request.form.get("desc")
        
        db.execute("INSERT INTO tasks(name,desc,user_id) VALUES (?,?,?)", name, desc, session["user_id"])

        return redirect("/")
    else:
        return render_template("new_task.html")


@app.route("/start_task", methods=["POST"])
@login_required
def start_task():
    # get taskId
    id = request.form.get("start")

    # change the state of the task
    db.execute("UPDATE tasks SET state = 2 WHERE id = ?", id)

    return redirect("/")


@app.route("/finish_task", methods=["POST"])
@login_required
def finish_task():
    # get task
    id = request.form.get("finish")

    # change state of the task
    db.execute("UPDATE tasks SET state = 3 WHERE id = ?", id)

    return redirect("/")


@app.route("/delete_task", methods=["POST"])
@login_required
def delete_task():
    # get task
    id = request.form.get("delete")

    # change state of the task
    db.execute("UPDATE tasks SET state = 0 WHERE id = ?", id)

    return redirect("/")


@app.route("/profile")
@login_required
def profile():
    name = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]["name"]
    deleted = db.execute("SELECT * FROM tasks WHERE state = 0 AND  user_id = ?", session["user_id"])

    return render_template("profile.html", deleted=deleted, name=name)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()

    return redirect("/")