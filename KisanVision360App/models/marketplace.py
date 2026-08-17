from app import db


class Marketplace(db.Model):

    __tablename__ = "marketplace_products"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    farmer_id = db.Column(
        db.Integer,
        nullable=True
    )

    product_name = db.Column(
        db.String(100),
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    quantity = db.Column(
        db.Float,
        nullable=False
    )

    unit = db.Column(
        db.String(20),
        default="Kg"
    )

    image = db.Column(
        db.String(255),
        default="no-image.png"
    )

    description = db.Column(
        db.Text
    )

    location = db.Column(
        db.String(150)
    )

    phone = db.Column(
        db.String(15)
    )

    status = db.Column(
        db.String(20),
        default="Available"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def __repr__(self):

        return f"<Marketplace {self.product_name}>"
