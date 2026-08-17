from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models.marketplace import Marketplace

marketplace_bp = Blueprint("marketplace", __name__)


# ------------------------------
# Marketplace Home
# ------------------------------

@marketplace_bp.route("/marketplace")
def marketplace():

    products = Marketplace.query.order_by(
        Marketplace.id.desc()
    ).all()

    return render_template(

        "marketplace/marketplace.html",

        products=products

    )


# ------------------------------
# Product Details
# ------------------------------

@marketplace_bp.route("/marketplace/product/<int:id>")
def product(id):

    product = Marketplace.query.get_or_404(id)

    return render_template(

        "marketplace/product.html",

        product=product

    )


# ------------------------------
# Add Product
# ------------------------------

@marketplace_bp.route("/marketplace/add",methods=["GET","POST"])
def add_product():

    if request.method=="POST":

        product = Marketplace(

            product_name=request.form["product_name"],

            category=request.form["category"],

            price=request.form["price"],

            quantity=request.form["quantity"],

            description=request.form["description"],

            image=request.form["image"]

        )

        db.session.add(product)

        db.session.commit()

        flash("Product Added Successfully")

        return redirect(url_for("marketplace.marketplace"))

    return render_template(

        "marketplace/add_product.html"

    )


# ------------------------------
# Edit Product
# ------------------------------

@marketplace_bp.route("/marketplace/edit/<int:id>",methods=["GET","POST"])
def edit_product(id):

    product=Marketplace.query.get_or_404(id)

    if request.method=="POST":

        product.product_name=request.form["product_name"]

        product.category=request.form["category"]

        product.price=request.form["price"]

        product.quantity=request.form["quantity"]

        product.description=request.form["description"]

        db.session.commit()

        flash("Updated Successfully")

        return redirect(url_for("marketplace.marketplace"))

    return render_template(

        "marketplace/edit_product.html",

        product=product

    )


# ------------------------------
# Delete Product
# ------------------------------

@marketplace_bp.route("/marketplace/delete/<int:id>")
def delete_product(id):

    product=Marketplace.query.get_or_404(id)

    db.session.delete(product)

    db.session.commit()

    flash("Deleted Successfully")

    return redirect(url_for("marketplace.marketplace"))


# ------------------------------
# Cart
# ------------------------------

@marketplace_bp.route("/cart")
def cart():

    return render_template(

        "marketplace/cart.html"

    )


# ------------------------------
# Checkout
# ------------------------------

@marketplace_bp.route("/checkout")
def checkout():

    return render_template(

        "marketplace/checkout.html"

    )


# ------------------------------
# Orders
# ------------------------------

@marketplace_bp.route("/orders")
def orders():

    return render_template(

        "marketplace/orders.html"

    )


# ------------------------------
# Wishlist
# ------------------------------

@marketplace_bp.route("/wishlist")
def wishlist():

    return render_template(

        "marketplace/wishlist.html"

    )
