from app import db
from datetime import datetime


class Marketplace(db.Model):

    __tablename__ = "marketplace_products"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =========================================================
    # FARMER
    # =========================================================

    farmer_id = db.Column(
        db.Integer,
        nullable=True,
        index=True
    )

    # =========================================================
    # PRODUCT INFORMATION
    # =========================================================

    product_name = db.Column(
        db.String(150),
        nullable=False,
        index=True
    )

    category = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    # =========================================================
    # PRICE & STOCK
    # =========================================================

    price = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    quantity = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    unit = db.Column(
        db.String(20),
        nullable=False,
        default="Kg"
    )

    # =========================================================
    # PRODUCT IMAGE
    # =========================================================

    image = db.Column(
        db.String(255),
        nullable=False,
        default="no-image.png"
    )

    # =========================================================
    # LOCATION
    # =========================================================

    location = db.Column(
        db.String(150),
        nullable=True,
        index=True
    )

    # =========================================================
    # CONTACT
    # =========================================================

    phone = db.Column(
        db.String(15),
        nullable=True
    )

    # =========================================================
    # PRODUCT STATUS
    # Available
    # Sold Out
    # Pending
    # Inactive
    # =========================================================

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Available",
        index=True
    )

    # =========================================================
    # CREATED / UPDATED
    # =========================================================

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # =========================================================
    # HELPER METHODS
    # =========================================================

    @property
    def is_available(self):

        return (
            self.status.lower() == "available"
            and self.quantity > 0
        )


    @property
    def total_stock_value(self):

        try:
            return float(self.price) * float(self.quantity)
        except (TypeError, ValueError):
            return 0.0


    @property
    def price_per_unit(self):

        try:
            return float(self.price)
        except (TypeError, ValueError):
            return 0.0


    def reduce_stock(self, amount):

        """
        Reduce product stock after an order.
        """

        try:

            amount = float(amount)

        except (TypeError, ValueError):

            raise ValueError(
                "Invalid quantity."
            )

        if amount <= 0:

            raise ValueError(
                "Quantity must be greater than zero."
            )

        if amount > self.quantity:

            raise ValueError(
                "Insufficient stock."
            )

        self.quantity -= amount

        if self.quantity <= 0:

            self.quantity = 0

            self.status = "Sold Out"

        else:

            self.status = "Available"


    def restore_stock(self, amount):

        """
        Restore stock when an order is cancelled.
        """

        try:

            amount = float(amount)

        except (TypeError, ValueError):

            raise ValueError(
                "Invalid quantity."
            )

        if amount <= 0:

            raise ValueError(
                "Quantity must be greater than zero."
            )

        self.quantity += amount

        self.status = "Available"


    def __repr__(self):

        return (
            f"<Marketplace "
            f"id={self.id} "
            f"product={self.product_name}>"
        )
