from flask import Flask, render_template, send_file,redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from datetime import datetime
from config import Config
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import func 
import io

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Models
class Product(db.Model):
    product_id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Product {self.product_id} - {self.name}>'

class Location(db.Model):
    location_id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Location {self.location_id} - {self.name}>'

class ProductMovement(db.Model):
    movement_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    from_location = db.Column(db.String(10), db.ForeignKey('location.location_id'), nullable=True)
    to_location = db.Column(db.String(10), db.ForeignKey('location.location_id'), nullable=True)
    product_id = db.Column(db.String(10), db.ForeignKey('product.product_id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    from_location_rel = db.relationship('Location', foreign_keys=[from_location], lazy='joined', backref='movements_from')
    to_location_rel = db.relationship('Location', foreign_keys=[to_location], lazy='joined', backref='movements_to')
    product_rel = db.relationship('Product', foreign_keys=[product_id], lazy='joined')

    def __repr__(self):
        return f'<Movement {self.movement_id} Product {self.product_id} Qty {self.qty}>'

# Forms
class ProductForm(FlaskForm):
    product_id = StringField('Product Code', validators=[DataRequired(), Length(max=10)])
    name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save')

class LocationForm(FlaskForm):
    location_id = StringField('Location Code', validators=[DataRequired(), Length(max=10)])
    name = StringField('Location Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save')

class ProductMovementForm(FlaskForm):
    timestamp = DateTimeField('Timestamp', default=datetime.utcnow, format='%Y-%m-%d %H:%M:%S', validators=[Optional()])
    product_id = SelectField('Product', coerce=str, validators=[DataRequired()])
    from_location = SelectField('From Location (leave blank if new stock)', coerce=str, validators=[Optional()])
    to_location = SelectField('To Location (leave blank if stock out)', coerce=str, validators=[Optional()])
    qty = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Save')

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        # At least one of from_location or to_location must be filled
        if not self.from_location.data and not self.to_location.data:
            self.from_location.errors.append('Either From Location or To Location must be specified.')
            self.to_location.errors.append('Either From Location or To Location must be specified.')
            return False
        # Both cannot be empty strings at the same time
        return True

# Routes - Products
@app.route('/')
@app.route('/products')
def product_list():
    products = Product.query.order_by(Product.product_id).all()
    return render_template('product_list.html', products=products)

@app.route('/product/add', methods=['GET', 'POST'])
def product_add():
    form = ProductForm()
    if form.validate_on_submit():
        exists = Product.query.filter_by(product_id=form.product_id.data).first()
        if exists:
            flash('Product code already exists.', 'danger')
            return render_template('product_form.html', form=form, title='Add Product')
        product = Product(product_id=form.product_id.data.strip(), name=form.name.data.strip())
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully.', 'success')
        return redirect(url_for('product_list'))
    return render_template('product_form.html', form=form, title='Add Product')

@app.route('/product/edit/<string:product_id>', methods=['GET', 'POST'])
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.product_id.render_kw = {'readonly': True}
    if form.validate_on_submit():
        product.name = form.name.data.strip()
        db.session.commit()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('product_list'))
    return render_template('product_form.html', form=form, title='Edit Product')

@app.route('/product/delete/<string:product_id>', methods=['POST'])
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    # Check for dependent movements
    movements = ProductMovement.query.filter_by(product_id=product_id).first()
    if movements:
        flash('Cannot delete product with existing movements.', 'danger')
        return redirect(url_for('product_list'))
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'success')
    return redirect(url_for('product_list'))

# Routes - Locations
@app.route('/locations')
def location_list():
    locations = Location.query.order_by(Location.location_id).all()
    return render_template('location_list.html', locations=locations)

@app.route('/location/add', methods=['GET', 'POST'])
def location_add():
    form = LocationForm()
    if form.validate_on_submit():
        exists = Location.query.filter_by(location_id=form.location_id.data).first()
        if exists:
            flash('Location code already exists.', 'danger')
            return render_template('location_form.html', form=form, title='Add Location')
        location = Location(location_id=form.location_id.data.strip(), name=form.name.data.strip())
        db.session.add(location)
        db.session.commit()
        flash('Location added successfully.', 'success')
        return redirect(url_for('location_list'))
    return render_template('location_form.html', form=form, title='Add Location')

@app.route('/location/edit/<string:location_id>', methods=['GET', 'POST'])
def location_edit(location_id):
    location = Location.query.get_or_404(location_id)
    form = LocationForm(obj=location)
    form.location_id.render_kw = {'readonly': True}
    if form.validate_on_submit():
        location.name = form.name.data.strip()
        db.session.commit()
        flash('Location updated successfully.', 'success')
        return redirect(url_for('location_list'))
    return render_template('location_form.html', form=form, title='Edit Location')

@app.route('/location/delete/<string:location_id>', methods=['POST'])
def location_delete(location_id):
    location = Location.query.get_or_404(location_id)
    # Check for dependent movements
    movements_from = ProductMovement.query.filter_by(from_location=location_id).first()
    movements_to = ProductMovement.query.filter_by(to_location=location_id).first()
    if movements_from or movements_to:
        flash('Cannot delete location with existing movements.', 'danger')
        return redirect(url_for('location_list'))
    db.session.delete(location)
    db.session.commit()
    flash('Location deleted.', 'success')
    return redirect(url_for('location_list'))

# Routes - Product Movements
@app.route('/movements')
def movement_list():
    movements = ProductMovement.query.order_by(ProductMovement.timestamp.desc()).all()
    return render_template('movement_list.html', movements=movements)

@app.route('/movement/add', methods=['GET', 'POST'])
def movement_add():
    form = ProductMovementForm()
    # Populate product and location choices
    form.product_id.choices = [(p.product_id, f'{p.product_id} - {p.name}') for p in Product.query.order_by(Product.product_id).all()]
    locations = [(None, '')] + [(l.location_id, f'{l.location_id} - {l.name}') for l in Location.query.order_by(Location.location_id).all()]
    form.from_location.choices = locations
    form.to_location.choices = locations

    if form.validate_on_submit():
        timestamp = form.timestamp.data or datetime.utcnow()
        from_loc = form.from_location.data or None
        to_loc = form.to_location.data or None
        movement = ProductMovement(
            timestamp=timestamp,
            from_location=from_loc,
            to_location=to_loc,
            product_id=form.product_id.data,
            qty=form.qty.data
        )
        db.session.add(movement)
        db.session.commit()
        flash('Product movement recorded.', 'success')
        return redirect(url_for('movement_list'))
    return render_template('movement_form.html', form=form, title='Add Product Movement')

@app.route('/movement/delete/<int:movement_id>', methods=['POST'])
def movement_delete(movement_id):
    movement = ProductMovement.query.get_or_404(movement_id)
    db.session.delete(movement)
    db.session.commit()
    flash('Movement deleted.', 'success')
    return redirect(url_for('movement_list'))

# Report: Balance quantity in each location per product
@app.route('/report')
def report():
    # Calculate balance using product movements
    # For each product and location, sum qty for to_location and subtract qty for from_location
    products = Product.query.all()
    locations = Location.query.all()

    # Build a dictionary {(product_id, location_id): balance_qty}
    balance = {}

    # Initialize balance dictionary keys
    for p in products:
        for l in locations:
            balance[(p.product_id, l.location_id)] = 0

    # Aggregate movements
    movements = ProductMovement.query.all()
    for m in movements:
        if m.to_location:
            key = (m.product_id, m.to_location)
            balance[key] = balance.get(key, 0) + m.qty
        if m.from_location:
            key = (m.product_id, m.from_location)
            balance[key] = balance.get(key, 0) - m.qty

    # Prepare data for template: list of dicts with product, location, qty > 0
    report_data = []
    for (pid, lid), qty in balance.items():
        if qty > 0:
            product = next((p for p in products if p.product_id == pid), None)
            location = next((l for l in locations if l.location_id == lid), None)
            if product and location:
                report_data.append({
                    'product_id': pid,
                    'product_name': product.name,
                    'location_id': lid,
                    'location_name': location.name,
                    'quantity': qty
                })

    return render_template('report.html', report_data=report_data)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500
def _get_report_data():
    """Return list of dicts: product_id, product_name, location_id, location_name, quantity (qty>0)."""
    products = Product.query.all()
    locations = Location.query.all()

    # initialize balances
    balance = {}
    for p in products:
        for l in locations:
            balance[(p.product_id, l.location_id)] = 0

    movements = ProductMovement.query.all()
    for m in movements:
        # add to destination
        if m.to_location:
            key = (m.product_id, m.to_location)
            balance[key] = balance.get(key, 0) + (m.qty or 0)
        # subtract from source
        if m.from_location:
            key = (m.product_id, m.from_location)
            balance[key] = balance.get(key, 0) - (m.qty or 0)

    report_data = []
    for (pid, lid), qty in balance.items():
        if qty > 0:
            product = next((p for p in products if p.product_id == pid), None)
            location = next((l for l in locations if l.location_id == lid), None)
            if product and location:
                report_data.append({
                    'product_id': pid,
                    'product_name': product.name,
                    'location_id': lid,
                    'location_name': location.name,
                    'quantity': qty
                })
    return report_data

@app.route('/download-report')
def download_report():
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    report_data = _get_report_data()

    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, height - 50, "Inventory Report")

    # Table headers
    pdf.setFont("Helvetica-Bold", 12)
    y = height - 100
    pdf.drawString(50, y, "Product")
    pdf.drawString(250, y, "Location")
    pdf.drawString(450, y, "Quantity")

    # Data rows
    pdf.setFont("Helvetica", 12)
    y -= 25
    for row in report_data:
        if y < 60:
            pdf.showPage()
            # re-draw header on new page
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(200, height - 50, "Inventory Report")
            pdf.setFont("Helvetica-Bold", 12)
            y = height - 100
            pdf.drawString(50, y, "Product")
            pdf.drawString(250, y, "Location")
            pdf.drawString(450, y, "Quantity")
            pdf.setFont("Helvetica", 12)
            y -= 25

        pdf.drawString(50, y, f"{row['product_id']} - {row['product_name']}")
        pdf.drawString(250, y, f"{row['location_id']} - {row['location_name']}")
        pdf.drawString(450, y, str(row['quantity']))
        y -= 20

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="inventory_report.pdf", mimetype='application/pdf')


if __name__ == '__main__':
    # Create DB tables if they don't exist (dev only)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
