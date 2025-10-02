from app import db, app  # assuming app.py defines both `app` and `db`

# Use the application context
with app.app_context():
    db.create_all()
    print("✅ Tables created successfully.")


