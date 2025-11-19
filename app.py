"""
app.py — Simple Inventory Dashboard (beginner-friendly)

How to run:
1. Create virtualenv and install requirements: pip install -r requirements.txt
2. (optional) python example_data.py
3. python app.py
4. Open http://127.0.0.1:5000/
"""

from flask import Flask, render_template, request, redirect, url_for, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from reportlab.pdfgen import canvas
import io

# ---------- Flask app and DB setup ----------
app = Flask(__name__)
app.config["SECRET_KEY"] = "inventory-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------- Models ----------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(10), unique=True, nullable=False)  # e.g. "P01"
    name = db.Column(db.String(100), nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.String(10), unique=True, nullable=False)  # e.g. "L01"
    name = db.Column(db.String(100), nullable=False)

class Movement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    product_id = db.Column(db.String(10), nullable=False)
    from_location = db.Column(db.String(10), nullable=True)
    to_location = db.Column(db.String(10), nullable=True)
    qty = db.Column(db.Integer, nullable=False)

# ---------- Helper: calculate stock ----------
def calculate_stock():
    """
    Build a nested dictionary:
      stock[product_id][location_id] = quantity (int)

    We initialize all product-location pairs to 0 so templates don't crash.
    """
    stock = {}
    products = Product.query.all()
    locations = Location.query.all()

    # initialize zeros
    for p in products:
        stock[p.product_id] = {}
        for loc in locations:
            stock[p.product_id][loc.location_id] = 0

    # apply movements (add to 'to_location', subtract from 'from_location')
    movements = Movement.query.all()
    for m in movements:
        # ensure product key exists (in case movement has a product not in products list)
        if m.product_id not in stock:
            stock[m.product_id] = {}
            for loc in locations:
                stock[m.product_id][loc.location_id] = 0

        if m.to_location:
            stock[m.product_id][m.to_location] += m.qty
        if m.from_location:
            stock[m.product_id][m.from_location] -= m.qty

    return stock

# ---------- Routes ----------
@app.route("/")
def dashboard():
    """Main page showing products, locations, movements and the stock report."""
    products = Product.query.order_by(Product.product_id).all()
    locations = Location.query.order_by(Location.location_id).all()
    movements = Movement.query.order_by(Movement.timestamp.desc()).all()
    stock = calculate_stock()
    return render_template("dashboard.html",
                           products=products,
                           locations=locations,
                           movements=movements,
                           stock=stock)

# ---------- Add actions ----------
@app.route("/add_product", methods=["POST"])
def add_product():
    pid = request.form.get("product_id", "").strip()
    name = request.form.get("name", "").strip()
    if not pid or not name:
        return "Product ID and name are required.", 400

    # prevent duplicate product_id
    if Product.query.filter_by(product_id=pid).first():
        return f"Product ID '{pid}' already exists.", 400

    # save
    new = Product(product_id=pid, name=name)
    db.session.add(new)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/add_location", methods=["POST"])
def add_location():
    lid = request.form.get("location_id", "").strip()
    name = request.form.get("name", "").strip()
    if not lid or not name:
        return "Location ID and name are required.", 400

    if Location.query.filter_by(location_id=lid).first():
        return f"Location ID '{lid}' already exists.", 400

    new = Location(location_id=lid, name=name)
    db.session.add(new)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/add_movement", methods=["POST"])
def add_movement():
    pid = request.form.get("product_id", "").strip()
    from_loc = request.form.get("from_location") or None
    to_loc = request.form.get("to_location") or None
    qty_raw = request.form.get("qty", "").strip()
    if not pid or not qty_raw:
        return "Product and quantity are required.", 400

    # qty must be positive integer
    try:
        qty = int(qty_raw)
    except ValueError:
        return "Quantity must be an integer.", 400
    if qty <= 0:
        return "Quantity must be positive.", 400

    # ensure product exists (user must add product first)
    if not Product.query.filter_by(product_id=pid).first():
        return f"Product ID '{pid}' does not exist.", 400

    mv = Movement(product_id=pid, from_location=from_loc, to_location=to_loc, qty=qty)
    db.session.add(mv)
    db.session.commit()
    return redirect(url_for("dashboard"))

# ---------- Delete actions (use POST for safety) ----------
@app.route("/delete_product/<int:id>", methods=["POST"])
def delete_product(id):
    prod = Product.query.get_or_404(id)
    # avoid deleting if movements reference this product
    if Movement.query.filter_by(product_id=prod.product_id).count() > 0:
        return "Cannot delete product referenced by movements.", 400
    db.session.delete(prod)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/delete_location/<int:id>", methods=["POST"])
def delete_location(id):
    loc = Location.query.get_or_404(id)
    # check any movement refers to this location
    if Movement.query.filter(
        (Movement.from_location == loc.location_id) | (Movement.to_location == loc.location_id)
    ).count() > 0:
        return "Cannot delete location referenced by movements.", 400
    db.session.delete(loc)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/delete_movement/<int:id>", methods=["POST"])
def delete_movement(id):
    mv = Movement.query.get_or_404(id)
    db.session.delete(mv)
    db.session.commit()
    return redirect(url_for("dashboard"))

# ---------- Export PDF ----------
@app.route("/export_pdf")
def export_pdf():
    """Create a simple PDF report showing stock per product & location."""
    stock = calculate_stock()
    products = Product.query.order_by(Product.product_id).all()
    locations = Location.query.order_by(Location.location_id).all()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    width, height = 595, 842  # A4-ish

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(width / 2.0, height - 40, "Inventory Stock Report")

    y = height - 80
    pdf.setFont("Helvetica", 11)
    line_height = 14

    for p in products:
        pdf.drawString(50, y, f"{p.product_id} - {p.name}")
        y -= line_height
        for l in locations:
            qty = stock.get(p.product_id, {}).get(l.location_id, 0)
            pdf.drawString(70, y, f"{l.name}: {qty}")
            y -= line_height
            if y < 60:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                y = height - 40
        y -= 6
        if y < 60:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            y = height - 40

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="inventory_report.pdf", mimetype="application/pdf")

# ---------- Bootstrap DB and run ----------
if __name__ == "__main__":
    # ensure tables are created
    with app.app_context():
        db.create_all()
    app.run(debug=True)
