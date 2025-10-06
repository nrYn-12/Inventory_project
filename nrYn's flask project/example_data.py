from app import app, db
from app import Product, Location, ProductMovement
from datetime import datetime, timedelta

with app.app_context():
    db.drop_all()
    db.create_all()

    # Create Products
    products = [
        Product(product_id='P01', name='Laptop'),
        Product(product_id='P02', name='Mobile'),
        Product(product_id='P03', name='Keyboard'),
        Product(product_id='P04', name='Mouse'),
    ]
    db.session.add_all(products)

    # Create Locations
    locations = [
        Location(location_id='L01', name='Chennai Warehouse'),
        Location(location_id='L02', name='Bangalore Warehouse'),
        Location(location_id='L03', name='Delhi Shop'),
    ]
    db.session.add_all(locations)
    db.session.commit()

    # Create Movements (20 movements)
    movements = [
        # Add 10 laptops into Chennai
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=20), from_location=None, to_location='L01', product_id='P01', qty=10),
        # Add 15 mobiles into Bangalore
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=19), from_location=None, to_location='L02', product_id='P02', qty=15),
        # Move 5 laptops from Chennai to Delhi
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=18), from_location='L01', to_location='L03', product_id='P01', qty=5),
        # Remove 2 mobiles from Bangalore (sold)
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=17), from_location='L02', to_location=None, product_id='P02', qty=2),
        # Add 7 keyboards into Chennai
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=16), from_location=None, to_location='L01', product_id='P03', qty=7),
        # Add 12 mice into Delhi shop
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=15), from_location=None, to_location='L03', product_id='P04', qty=12),
        # Transfer 3 keyboards from Chennai to Bangalore
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=14), from_location='L01', to_location='L02', product_id='P03', qty=3),
        # Remove 1 mouse from Delhi shop (sold)
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=13), from_location='L03', to_location=None, product_id='P04', qty=1),
        # Add 8 mobiles into Chennai
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=12), from_location=None, to_location='L01', product_id='P02', qty=8),
        # Transfer 4 mobiles from Chennai to Delhi
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=11), from_location='L01', to_location='L03', product_id='P02', qty=4),
        # Add 6 laptops into Bangalore
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=10), from_location=None, to_location='L02', product_id='P01', qty=6),
        # Remove 2 keyboards from Bangalore (sold)
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=9), from_location='L02', to_location=None, product_id='P03', qty=2),
        # Add 5 mice into Bangalore
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=8), from_location=None, to_location='L02', product_id='P04', qty=5),
        # Transfer 2 mice from Bangalore to Chennai
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=7), from_location='L02', to_location='L01', product_id='P04', qty=2),
        # Add 3 keyboards into Delhi
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=6), from_location=None, to_location='L03', product_id='P03', qty=3),
        # Remove 1 laptop from Delhi (sold)
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=5), from_location='L03', to_location=None, product_id='P01', qty=1),
        # Transfer 4 laptops from Bangalore to Chennai
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=4), from_location='L02', to_location='L01', product_id='P01', qty=4),
        # Add 10 mobiles into Delhi
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=3), from_location=None, to_location='L03', product_id='P02', qty=10),
        # Remove 3 mice from Chennai (sold)
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=2), from_location='L01', to_location=None, product_id='P04', qty=3),
        # Transfer 2 mobiles from Delhi to Bangalore
        ProductMovement(timestamp=datetime.utcnow() - timedelta(days=1), from_location='L03', to_location='L02', product_id='P02', qty=2),
    ]
    db.session.add_all(movements)
    db.session.commit()
    print("Sample data inserted successfully.")
