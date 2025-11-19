from app import db, Product, Location, Movement, app
from datetime import datetime

with app.app_context():
    db.drop_all()
    db.create_all()

    # Sample Products
    p1 = Product(product_id="P01", name="Laptop")
    p2 = Product(product_id="P02", name="Mobile")
    p3 = Product(product_id="P03", name="Keyboard")

    # Sample Locations
    l1 = Location(location_id="L01", name="Chennai Warehouse")
    l2 = Location(location_id="L02", name="Bangalore Warehouse")

    db.session.add_all([p1, p2, p3, l1, l2])
    db.session.commit()

    # Sample Movements
    m1 = Movement(product_id="P01", to_location="L01", qty=10)
    m2 = Movement(product_id="P02", to_location="L02", qty=20)
    m3 = Movement(product_id="P01", from_location="L01", to_location="L02", qty=3)

    db.session.add_all([m1, m2, m3])
    db.session.commit()

    print("Sample data inserted!")
