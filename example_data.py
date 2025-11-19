# example_data.py — safe & simple sample data inserter
# Usage: stop the server, then run `python example_data.py`

from app import app, db, Product, Location, Movement
from datetime import datetime

def add_if_missing(model, **kwargs):
    """Return existing row or create new one (no duplicates)."""
    obj = model.query.filter_by(**{k: kwargs[k] for k in kwargs if k in model.__table__.columns}).first()
    if obj:
        return obj
    obj = model(**kwargs)
    db.session.add(obj)
    return obj

with app.app_context():
    db.create_all()

    # products
    add_if_missing(Product, product_id="P01", name="Laptop")
    add_if_missing(Product, product_id="P02", name="Mobile")
    add_if_missing(Product, product_id="P03", name="Keyboard")

    # locations
    add_if_missing(Location, location_id="L01", name="Chennai Warehouse")
    add_if_missing(Location, location_id="L02", name="Bangalore Warehouse")

    # movements (we keep them simple; duplicates are allowed but harmless)
    if not Movement.query.filter_by(product_id="P01", to_location="L01", qty=10).first():
        db.session.add(Movement(product_id="P01", to_location="L01", qty=10, timestamp=datetime.utcnow()))
    if not Movement.query.filter_by(product_id="P02", to_location="L02", qty=20).first():
        db.session.add(Movement(product_id="P02", to_location="L02", qty=20, timestamp=datetime.utcnow()))
    if not Movement.query.filter_by(product_id="P01", from_location="L01", to_location="L02", qty=3).first():
        db.session.add(Movement(product_id="P01", from_location="L01", to_location="L02", qty=3, timestamp=datetime.utcnow()))

    db.session.commit()
    print("Sample data inserted (if missing).")
