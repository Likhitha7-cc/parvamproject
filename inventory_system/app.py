from flask import Flask, render_template, request, redirect, session
import json, os

app = Flask(__name__)
app.secret_key = "secret123"

INV_FILE = "inventory.json"
USER_FILE = "users.json"

# Ensure files exist
for file, default in [
    (INV_FILE, {"products": []}),
    (USER_FILE, {"users": [{"username": "admin", "password": "admin123", "role": "admin"}, {"username": "user", "password": "user123", "role": "user"}]})
]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)

def load(file):
    with open(file, "r") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load(USER_FILE)["users"]

        for u in users:
            if u["username"] == username and u["password"] == password:
                session["user"] = username
                session["role"] = u["role"]
                if u["role"] == "admin":
                    return redirect("/admin")
                else:
                    return redirect("/")

        return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/login")

    products = load(INV_FILE)["products"]
    users = load(USER_FILE)["users"]
    
    low_count = 0
    for p in products:
        p["status"] = "Low Stock" if p["quantity"] < p["min_threshold"] else "OK"
        if p["status"] == "Low Stock":
            low_count += 1

    return render_template("admin.html", products=products, users=users, low_count=low_count)

# (Removed duplicate add_product route)
# ---------------- ADD USER ----------------
@app.route("/add_user", methods=["POST"])
def add_user():
    if not is_admin():
        return "Access Denied"

    data = load(USER_FILE)

    new_user = {
        "username": request.form["username"],
        "password": request.form["password"],
        "role": "user"
    }

    data["users"].append(new_user)
    save(USER_FILE, data)

    return redirect("/admin")

# ---------------- USER VIEW ----------------
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")
    products = load(INV_FILE)["products"]
    low_count = 0

    for p in products:
        p["status"] = "Low Stock" if p["quantity"] < p["min_threshold"] else "OK"
        if p["status"] == "Low Stock":
            low_count += 1

    return render_template("index.html", products=products, low_count=low_count)



def is_admin():
    return session.get("role") == "admin"

@app.route("/add_product", methods=["POST"])
def add_product():
    if not is_admin():
        return "Access Denied"

    data = load(INV_FILE)

    new_product = {
        "id": len(data["products"]) + 1,
        "name": request.form["name"],
        "category": request.form["category"],
        "quantity": int(request.form["quantity"]),
        "min_threshold": int(request.form["threshold"])
    }

    data["products"].append(new_product)
    save(INV_FILE, data)

    return redirect("/admin")

@app.route("/delete/<int:id>")
def delete_product(id):
    if not is_admin():
        return "Access Denied"

    data = load(INV_FILE)
    data["products"] = [p for p in data["products"] if p["id"] != id]
    save(INV_FILE, data)

    return redirect("/admin")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    data = load(INV_FILE)
    product = next((p for p in data["products"] if p["id"] == id), None)

    if request.method == "POST":
        product["name"] = request.form["name"]
        product["category"] = request.form["category"]
        product["quantity"] = int(request.form["quantity"])
        product["min_threshold"] = int(request.form["threshold"])

        save(INV_FILE, data)
        return redirect("/admin")

    return render_template("edit_product.html", p=product)

if __name__ == "__main__":
    app.run(debug=True)
