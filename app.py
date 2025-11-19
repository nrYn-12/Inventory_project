from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)
app.config["SECRET_KEY"] = "inventory-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------------------------------------------
# MODELS
# ---------------------------------------------------

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

class Movement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    product_id = db.Column(db.String(10), nullable=False)
    from_location = db.Column(db.String(10), nullable=True)
    to_location = db.Column(db.String(10), nullable=True)
    qty = db.Column(db.Integer, nullable=False)

# ---------------------------------------------------
# CALCULATE STOCK
# ---------------------------------------------------

def calculate_stock():
    stock = {}
    products = Product.query.all()
    locations = Location.query.all()

    for p in products:
        stock[p.product_id] = {loc.location_id: 0 for loc in locations}

    for m in Movement.query.all():
        if m.to_location:
            stock[m.product_id][m.to_location] += m.qty
        if m.from_location:
            stock[m.product_id][m.from_location] -= m.qty

    return stock

# ---------------------------------------------------
# ROUTES
# ---------------------------------------------------

@app.route("/")
def dashboard():
    products = Product.query.all()
    locations = Location.query.all()
    movements = Movement.query.order_by(Movement.timestamp.desc()).all()
    stock = calculate_stock()
    return render_template("dashboard.html", products=products, locations=locations, movements=movements, stock=stock)

# -------------------------
# ADD actions
# -------------------------

@app.route("/add_product", methods=["POST"])
def add_product():
    db.session.add(Product(
        product_id=request.form["product_id"],
        name=request.form["name"]
    ))
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/add_location", methods=["POST"])
def add_location():
    db.session.add(Location(
        location_id=request.form["location_id"],
        name=request.form["name"]
    ))
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/add_movement", methods=["POST"])
def add_movement():
    db.session.add(Movement(
        product_id=request.form["product_id"],
        from_location=request.form.get("from_location") or None,
        to_location=request.form.get("to_location") or None,
        qty=int(request.form["qty"])
    ))
    db.session.commit()
    return redirect(url_for("dashboard"))

# -------------------------
# DELETE actions
# -------------------------

@app.route("/delete_product/<int:id>")
def delete_product(id):
    db.session.delete(Product.query.get(id))
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/delete_location/<int:id>")
def delete_location(id):
    db.session.delete(Location.query.get(id))
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/delete_movement/<int:id>")
def delete_movement(id):
    db.session.delete(Movement.query.get(id))
    db.session.commit()
    return redirect(url_for("dashboard"))

# -------------------------
# EXPORT PDF
# -------------------------

@app.route("/export_pdf")
def export_pdf():
    stock = calculate_stock()
    products = Product.query.all()
    locations = Location.query.all()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 800, "Inventory Stock Report")

    y = 760
    pdf.setFont("Helvetica", 12)

    for p in products:
        pdf.drawString(50, y, f"{p.product_id} - {p.name}")
        y -= 20
        for l in locations:
            pdf.drawString(70, y, f"{l.name}: {stock[p.product_id][l.location_id]}")
            y -= 15
        y -= 10

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="inventory_report.pdf")

# ---------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
