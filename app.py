import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd, prs

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["prs"] = prs

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
os.environ["API_KEY"] = "pk_4194e8352e074ad4ba0cf2dbf9d2c2ea"
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")



@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    rows=db.execute("SELECT cash FROM users WHERE id=:user_id", user_id =session["user_id"])
    stock=db.execute("SELECT symbol, SUM(shares) as total_shares FROM registerss WHERE :user_id GROUP BY symbol HAVING total_shares>0",
    user_id=session["user_id"])
    stocks={}

    total_asset = 0
    for stockss in stock:
        stocks[stockss["symbol"]] = lookup(stockss["symbol"])
        total_asset += stocks[stockss["symbol"]]["price"]*stockss["total_shares"]

    cashremain=rows[0]["cash"]

    print(stock)
    return render_template("home.html",stocks=stocks,stock=stock,cashremain=cashremain,total_asset=total_asset)










@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method=="POST":
         if not request.form.get("symbol"):
            return apology("must provide correct Symbol")

         if not request.form.get("shares"):
            return apology("must provide correct Share")

         if not request.form.get("shares").isdigit():
            return apology("Invalid shares")

         symbol=request.form.get("symbol").upper()
         share = int(request.form.get("shares"))
         stock=lookup(symbol)

         if stock is None:
            return apology("invalid symbol")

         row=db.execute("SELECT cash FROM users WHERE id=:user_id", user_id =session["user_id"])
         cashremain=row[0]["cash"]
         pershareprice= stock["price"]
         totprice= pershareprice*share

         if totprice > cashremain:
            return apology("can't afford")

         db.execute("UPDATE users SET cash=cash - :price WHERE id=:user_id",
            price=totprice,user_id=session["user_id"])





         db.execute("""INSERT INTO registerss (user_id, symbol, shares, price)
            VALUES (:user_id, :symbol, :shares, :price)
            """,
            user_id=session["user_id"],
            symbol=stock["symbol"],
            shares=share,
            price=stock["price"])

         flash("Bought!")
         return redirect("/")

    else:
         return render_template("buy.html")




@app.route("/change_password", methods=["GET", "POST"])
@login_required
def changepassword():
    """change password """
    if request.method == "POST":


        if not request.form.get("currentpassword"):
            return apology("must provide username")

        rows=db.execute("SELECT hash FROM users WHERE user_id = :user_id", user_id=session["user_id"])

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("currentpassword")):
            return apology("invalid password")

        if not request.form.get("newpassword"):
            return apology("must provide new password")

        elif not request.form.get("newpasswordconfirm"):
            return apology("must provide new password confirmation")

        elif request.form.get("newpassword") != request.form.get("newpasswordconfirm"):
            return apology("new password and confirmation password need to match")

        hash = generate_password_hash(request.form.get("newpassword"))
        rows = db.execute("UPDATE users SET hash = :hash WHERE id = :user_id", user_id=session["user_id"], hash=hash)

        # Show flash
        flash("Changed!")

    return render_template("changepassword.html")












@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    rows=db.execute("SELECT symbol, shares, price, time FROM registerss WHERE user_id = :user_id ORDER BY time ASC", user_id=session["user_id"])
    return render_template("history.html", rows=rows)







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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method=="POST":
        symbol = request.form.get("symbol").upper()
        stock=lookup(symbol)
        if stock == None:
            return apology("Stock not found")
        return render_template("quoted.html",stock=stock)
    else:
        return render_template("quote.html", greet="hi")



















@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    if request.method=="POST":
        if not request.form.get("username"):
            return apology("must provide username")

        if not request.form.get("password"):
            return apology("must provide password")


        key=db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", 
            username=request.form.get("username"),
            hash=generate_password_hash(request.form.get("password")))
        if key is None:
            return apology("error")
        session["user_id"] = key
        return redirect("/")
    else:
        return render_template("register.html")
















@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method=="POST":
         if not request.form.get("symbol"):
            return apology("must provide correct Symbol")

         if not request.form.get("shares"):
            return apology("must provide correct Share")

         if not request.form.get("shares").isdigit():
            return apology("Invalid shares")

         symbol=request.form.get("symbol").upper()
         share = int(request.form.get("shares"))
         stock_data=lookup(symbol)

         if stock_data is None:
            return apology("invalid symbol")

         if share <=0:
             return apology("less than 1 share, sorry")

         stock = db.execute("SELECT SUM(shares) as total_shares FROM registerss WHERE user_id = :user_id AND symbol = :symbol GROUP BY symbol",
                           user_id=session["user_id"], symbol=request.form.get("symbol"))

         if len(stock) != 1 or stock[0]["total_shares"] <= 0 or stock[0]["total_shares"] < share:
            return apology("you can't sell less than 0 or more than you own", 400)

         rows = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])

         cashremain = rows[0]["cash"]
         pershareprice = stock_data["price"]
         totprice= pershareprice*share

         db.execute("UPDATE users SET cash=:cash + :price WHERE id=:user_id",
                cash=cashremain,price=totprice,user_id=session["user_id"])





         db.execute("""INSERT INTO registerss (user_id, shares, price,symbol)
            VALUES (:user_id,  :shares, :price, :symbol)
            """,
            user_id=session["user_id"],
            symbol=symbol,
            shares=-share,
            price=pershareprice)

         flash("Sold!")
         return redirect("/")
    else:
        register=db.execute(
            "SELECT symbol, SUM(shares) as total_shares FROM registerss WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id=session["user_id"])
        return render_template("sell.html",register=register)






def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


if __name__ == '__main__':
    app.run(debug=False)