import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd, checkTable, getAvg, findInTable


# TO RUN APPLICATION: flask --app app --debug run


# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Need to create something to update the values everytime the user goes to the page
# Need to total all the amounts of the stock based on ticker and add them up based on price purchased
@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    name = db.execute(
        "SELECT username FROM users where id=?", session.get('user_id')
    )

    holdings = db.execute(
        "select * from holdings where name=?", name[0]["username"]
    )
    
    # Need to create something for account val
    return render_template("index.html",name = name[0]["username"], holdings=holdings)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    name = db.execute(
            "SELECT username FROM users where id=?", session.get('user_id')
        )
    
    amt = db.execute(
            "SELECT cash FROM users where username=?", name[0]["username"]
        )[0]["cash"]
    

    if request.method == "POST":
        
        
        print(name[0]["username"])

        #Getting Username
        

        print(amt)
        #Get Symbol and price associated with it
        session["ticker"] = request.form.get("symbol")
        ticker = lookup(session.get('ticker'))
        if ticker == None:
            return apology("Invalid Ticker")
        

        totalCost = ticker['price'] * int(request.form.get("shares"))
        if  totalCost > amt:
            return apology("not enough funds")
        
        #Validate if table exists, if not create it
        if checkTable("transactions",db) == None:
            db.execute(
                "CREATE TABLE transactions (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name varchar(225), ticker varchar(225), price int, quantity int, total int, date date, type varchar(225))"
            )
        # print(db.execute(
        #     "SELECT * FROM holdings"
        # ))
        t = datetime.now()
        #Insert the purchase data into the new table
        db.execute(
            "INSERT INTO  transactions (name, ticker, price, quantity, total, date, type) VALUES (?, ?, ?, ?, ?, ?, ?)", name[0]["username"],ticker['symbol'], ticker['price'], request.form.get("shares"), totalCost, t, "BUY"
        )

        table = checkTable("holdings",db)
        # Totals the amount of shares and total price of the amount of shares
        if  table == -1:
            db.execute(
                "CREATE TABLE holdings (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name varchar(225), ticker varchar(225), quantity int, total int)"
            )
            db.execute (
                "INSERT INTO holdings (name, ticker, quantity, total) VALUES (?, ?, ?, ?)", name[0]["username"],ticker['symbol'], request.form.get("shares"), ticker['price'] * int(request.form.get("shares"))
            )
        elif table == 1:
            db.execute (
                "INSERT INTO holdings (name, ticker, quantity, total) VALUES (?, ?, ?, ?)", name[0]["username"],ticker['symbol'], request.form.get("shares"), ticker['price'] * int(request.form.get("shares"))
            )
        else:
            inTbl = findInTable("holdings", db, ticker['symbol'].upper())

            if inTbl == 0:
                db.execute(
                    "UPDATE holdings SET quantity=quantity + ?, total= total + ? WHERE name == ? AND ticker == ?",  request.form.get("shares"), ticker['price'] * int(request.form.get("shares")),  name[0]["username"], ticker['symbol']
                )
            else:
                db.execute (
                    "INSERT INTO holdings (name, ticker, quantity, total) VALUES (?, ?, ?, ?)", name[0]["username"],ticker['symbol'], request.form.get("shares"), ticker['price'] * int(request.form.get("shares"))
                )
        
        # db.execute

        #Update user table with correct cash
        db.execute(
            "UPDATE users SET cash = ? WHERE username = ?", amt - totalCost, name[0]["username"]
        )
        
        amt = db.execute(
            "SELECT cash FROM users where username=?", name[0]["username"]
        )[0]["cash"]



        return render_template("buy.html",amount = amt)
    else:
        return render_template("buy.html",amount = amt)
    


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    name = db.execute(
        "SELECT username FROM users where id=?", session.get('user_id')
    )

    transactions = db.execute(
        "select * from transactions where name=?", name[0]["username"]
    )
    
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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


# @app.route("/quote", methods=["GET", "POST"])
# @login_required
# def quote():
    
#     """Get stock quote."""
#     if request.method == "POST":
#         session["ticker"] = request.form.get("symbol")
#         return redirect("/quoted")
#     return render_template("quote.html")

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quoted():
    
    """Get stock quote."""
    if request.method == "POST":
        session["ticker"] = request.form.get("symbol")
        ticker = lookup(session.get('ticker'))
        if ticker == None:
            return apology("Invalid Ticker")
        
        print(ticker)
        print(ticker['symbol'])
        print(ticker['price'])
        
        

        return render_template("quote.html", symbol = ticker['symbol'], price=ticker['price'])
    return render_template("quote.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure Passwords Match
        if request.form.get('password') != request.form.get('confirmPassword'):
            return apology("Passwords Do Not Match")
        
        
        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if len(rows) != 0:
            return apology("Username already exists")
        
        pw = generate_password_hash(request.form.get("password"))
        user = request.form.get("username")
        print(pw)
        print(user)
        
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)", user, pw
        )
        

        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    # Get the stock the user wants to sell 
    # get the amount of shares the user wants to sell
    #   Validate they have the amount of shares, if so sell it if not, throw an error
    # pull amount purchased from db store in a variable
    # Pull correct value from API
    # Subtract the quantity and total value from holdings
    # Update users cash amount 
    # update transactions db with the sale


    """Sell shares of stock"""
    if request.method == "POST":
        if not request.form.get("stockList"):
            return render_template("sell.html", holdings=db.execute("select * from holdings where name='dar'"))
        
        
        
        shares = int(request.form.get("quantity"))
        holding = db.execute(
            "SELECT * FROM holdings WHERE ticker==?", request.form.get("stockList")
        )
        name = holding[0]["name"]

        if shares > holding[0]["quantity"]:
            return apology("Do not own that much shares")
        
        stockPrice = lookup(name)

        if shares < holding[0]["quantity"]:
            db.execute(
                "UPDATE holdings SET quantity = quantity - ?, total =? WHERE name==? AND ticker==?" , int(shares), holding[0]["total"] - (holding[0]["total"]/holding[0]["quantity"]), name, holding[0]["ticker"]
            )
        elif shares == holding[0]["quantity"]:
            db.execute(
                "DELETE FROM holdings WHERE name==? AND ticker==?", name, holding[0]["ticker"]
            )


        db.execute(
                "INSERT INTO transactions (name, ticker, price, quantity, total, date, type) VALUES (?,?,?,?,?,?,?)", name, holding[0]["ticker"], (holding[0]["total"]/holding[0]["quantity"]), int(shares), (holding[0]["total"]/holding[0]["quantity"]) * shares, datetime.now(), "SELL"
        )
        db.execute(
                "UPDATE users SET cash= cash + ? WHERE username==?",  (holding[0]["total"]/holding[0]["quantity"]) * shares, name
        )
        print(name)
        return redirect("/")
    else:
        return render_template("sell.html", holdings=db.execute("select * from holdings where name='dar'"))
