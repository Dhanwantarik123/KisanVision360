# =========================================================
# KISANVISION360+
# MARKETPLACE ROUTES
# Flask + PostgreSQL / Supabase
# =========================================================

import os
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from werkzeug.utils import secure_filename

from database.db import get_db_connection


# =========================================================
# BLUEPRINT
# =========================================================

marketplace_bp = Blueprint(
    "marketplace",
    __name__
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "uploads",
    "products"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# DATABASE HELPER
# =========================================================

def get_db():
    """
    PostgreSQL connection through central database layer.
    """
    return get_db_connection()


# =========================================================
# AUTH HELPERS
# =========================================================

def logged_in():
    return "user_id" in session


def current_role():
    return str(
        session.get("role", "")
    ).strip().lower()


def farmer_only():
    return (
        logged_in()
        and current_role() == "farmer"
    )


def consumer_only():
    return (
        logged_in()
        and current_role() == "consumer"
    )


def login_redirect():
    """
    Blueprint-safe login redirect.
    """
    return redirect(
        url_for("auth.login")
    )


# =========================================================
# DATABASE COMPATIBILITY
# =========================================================

def row_to_dict(row):
    """
    Works with psycopg2 RealDictRow,
    dictionaries and normal tuples.
    """
    if row is None:
        return None

    if isinstance(row, dict):
        return dict(row)

    try:
        return dict(row)
    except Exception:
        return row


def rows_to_dict(rows):
    return [
        row_to_dict(row)
        for row in rows
    ]


def execute_fetchone(
    conn,
    query,
    params=()
):
    """
    PostgreSQL cursor helper.
    """
    with conn.cursor() as cur:
        cur.execute(
            query,
            params
        )
        return cur.fetchone()


def execute_fetchall(
    conn,
    query,
    params=()
):
    """
    PostgreSQL cursor helper.
    """
    with conn.cursor() as cur:
        cur.execute(
            query,
            params
        )
        return cur.fetchall()


# =========================================================
# TABLE INITIALIZATION
# =========================================================

def create_marketplace_tables():
    """Backward-compatible wrapper around the central DB initializer."""
    try:
        from database.db import init_db
        init_db()
        return True
    except Exception as e:
        print("MARKETPLACE TABLE INIT ERROR:", repr(e))
        return False


# =========================================================
# MARKETPLACE INTELLIGENCE
# =========================================================

def get_stock_status(quantity):

    try:
        quantity = float(
            quantity or 0
        )
    except Exception:
        quantity = 0

    if quantity <= 0:
        return "out_of_stock"

    if quantity <= 5:
        return "low_stock"

    if quantity <= 20:
        return "medium_stock"

    return "healthy_stock"


def get_product_intelligence(product):

    quantity = float(
        product.get("quantity", 0) or 0
    )

    price = float(
        product.get("price", 0) or 0
    )

    stock_status = get_stock_status(
        quantity
    )

    if stock_status == "out_of_stock":
        stock_score = 0

    elif stock_status == "low_stock":
        stock_score = 35

    elif stock_status == "medium_stock":
        stock_score = 70

    else:
        stock_score = 100

    quality_score = 70

    if price > 0:
        quality_score += 10

    if product.get("description"):
        quality_score += 10

    if product.get("image"):
        quality_score += 10

    quality_score = min(
        quality_score,
        100
    )

    return {
        "stock_status": stock_status,
        "stock_score": stock_score,
        "listing_score": quality_score,
        "stock_value": round(
            quantity * price,
            2
        )
    }


# =========================================================
# FARMER MARKETPLACE
# =========================================================

@marketplace_bp.route(
    "/farmer/marketplace"
)
def farmer_marketplace():

    if not farmer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        products = execute_fetchall(
            conn,
            """
            SELECT *
            FROM marketplace_products
            WHERE farmer_id = %s
            ORDER BY id DESC
            """,
            (
                session["user_id"],
            )
        )

        products = rows_to_dict(
            products
        )

        for product in products:
            product.update(
                get_product_intelligence(
                    product
                )
            )

        return render_template(
            "farmer_marketplace.html",
            products=products
        )

    except Exception as e:

        print(
            "FARMER MARKETPLACE ERROR:",
            repr(e)
        )

        return render_template(
            "farmer_marketplace.html",
            products=[]
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# FARMER PRODUCTS
# =========================================================

@marketplace_bp.route(
    "/farmer/products"
)
def farmer_products():

    if not farmer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        products = execute_fetchall(
            conn,
            """
            SELECT *
            FROM marketplace_products
            WHERE farmer_id = %s
            ORDER BY id DESC
            """,
            (
                session["user_id"],
            )
        )

        products = rows_to_dict(
            products
        )

        for product in products:
            product.update(
                get_product_intelligence(
                    product
                )
            )

        return render_template(
            "farmer_products.html",
            products=products
        )

    except Exception as e:

        print(
            "FARMER PRODUCTS ERROR:",
            repr(e)
        )

        return render_template(
            "farmer_products.html",
            products=[]
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# ADD PRODUCT
# =========================================================

@marketplace_bp.route("/add-product", methods=["GET", "POST"])
def add_product():

    if not farmer_only():
        return login_redirect()

    if request.method == "GET":

        return render_template(
            "add_product.html"
        )

    conn = None

    try:

        product_name = request.form.get(
            "product_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        unit = request.form.get(
            "unit",
            "Kg"
        ).strip() or "Kg"

        try:
            price = float(
                request.form.get(
                    "price",
                    0
                )
            )
        except Exception:
            price = 0

        try:
            quantity = float(
                request.form.get(
                    "quantity",
                    0
                )
            )
        except Exception:
            quantity = 0

        if not product_name:

            flash(
                "Product name is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "marketplace.add_product"
                )
            )

        if price < 0:

            flash(
                "Price cannot be negative.",
                "danger"
            )

            return redirect(
                url_for(
                    "marketplace.add_product"
                )
            )

        if quantity < 0:

            flash(
                "Quantity cannot be negative.",
                "danger"
            )

            return redirect(
                url_for(
                    "marketplace.add_product"
                )
            )

        # -------------------------------------------------
        # IMAGE
        # -------------------------------------------------

        image_name = "no-image.png"

        image = request.files.get(
            "image"
        )

        if image and image.filename:

            filename = secure_filename(
                image.filename
            )

            if filename:

                timestamp = datetime.now().strftime(
                    "%Y%m%d%H%M%S%f"
                )

                filename = (
                    timestamp
                    + "_"
                    + filename
                )

                image.save(
                    os.path.join(
                        UPLOAD_FOLDER,
                        filename
                    )
                )

                image_name = filename

        status = (
            "active"
            if quantity > 0
            else "inactive"
        )

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO marketplace_products
                (
                    farmer_id,
                    product_name,
                    category,
                    description,
                    price,
                    quantity,
                    unit,
                    image,
                    location,
                    status,
                    created_at,
                    updated_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """,
                (
                    session["user_id"],
                    product_name,
                    category,
                    description,
                    price,
                    quantity,
                    unit,
                    image_name,
                    location,
                    status
                )
            )

        conn.commit()

        flash(
            "Product added successfully!",
            "success"
        )

        return redirect(
            url_for(
                "marketplace.farmer_products"
            )
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "ADD PRODUCT ERROR:",
            repr(e)
        )

        flash(
            "Unable to add product.",
            "danger"
        )

        return redirect(
            url_for(
                "marketplace.add_product"
            )
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# EDIT PRODUCT
# =========================================================

@marketplace_bp.route(
    "/farmer/products/edit/<int:product_id>",
    methods=["GET", "POST"]
)
def edit_product(product_id):

    if not farmer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        product = execute_fetchone(
            conn,
            """
            SELECT *
            FROM marketplace_products
            WHERE id = %s
              AND farmer_id = %s
            """,
            (
                product_id,
                session["user_id"]
            )
        )

        product = row_to_dict(
            product
        )

        if not product:

            flash(
                "Product not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "marketplace.farmer_products"
                )
            )

        if request.method == "GET":

            return render_template(
                "edit_product.html",
                product=product
            )

        product_name = request.form.get(
            "product_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        unit = request.form.get(
            "unit",
            "Kg"
        ).strip() or "Kg"

        try:
            price = float(
                request.form.get(
                    "price",
                    0
                )
            )
        except Exception:
            price = 0

        try:
            quantity = float(
                request.form.get(
                    "quantity",
                    0
                )
            )
        except Exception:
            quantity = 0

        if not product_name:

            flash(
                "Product name is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "marketplace.edit_product",
                    product_id=product_id
                )
            )

        if price < 0 or quantity < 0:

            flash(
                "Price and quantity cannot be negative.",
                "danger"
            )

            return redirect(
                url_for(
                    "marketplace.edit_product",
                    product_id=product_id
                )
            )

        image_name = (
            product.get("image")
            or "no-image.png"
        )

        image = request.files.get(
            "image"
        )

        if image and image.filename:

            filename = secure_filename(
                image.filename
            )

            if filename:

                timestamp = datetime.now().strftime(
                    "%Y%m%d%H%M%S%f"
                )

                filename = (
                    timestamp
                    + "_"
                    + filename
                )

                image.save(
                    os.path.join(
                        UPLOAD_FOLDER,
                        filename
                    )
                )

                image_name = filename

        status = (
            "active"
            if quantity > 0
            else "inactive"
        )

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE marketplace_products
                SET
                    product_name = %s,
                    category = %s,
                    description = %s,
                    price = %s,
                    quantity = %s,
                    unit = %s,
                    image = %s,
                    location = %s,
                    status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND farmer_id = %s
                """,
                (
                    product_name,
                    category,
                    description,
                    price,
                    quantity,
                    unit,
                    image_name,
                    location,
                    status,
                    product_id,
                    session["user_id"]
                )
            )

        conn.commit()

        flash(
            "Product updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "marketplace.farmer_products"
            )
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "EDIT PRODUCT ERROR:",
            repr(e)
        )

        flash(
            "Unable to update product.",
            "danger"
        )

        return redirect(
            url_for(
                "marketplace.farmer_products"
            )
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# DELETE PRODUCT
# =========================================================

@marketplace_bp.route(
    "/farmer/products/delete/<int:product_id>",
    methods=["POST"]
)
def delete_product(product_id):

    if not farmer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = None

    try:

        conn = get_db()

        product = execute_fetchone(
            conn,
            """
            SELECT id
            FROM marketplace_products
            WHERE id = %s
              AND farmer_id = %s
            """,
            (
                product_id,
                session["user_id"]
            )
        )

        if not product:

            return jsonify({
                "success": False,
                "message": "Product not found."
            }), 404

        with conn.cursor() as cur:

            cur.execute(
                """
                DELETE FROM wishlist
                WHERE product_id = %s
                """,
                (product_id,)
            )

            cur.execute(
                """
                DELETE FROM cart
                WHERE product_id = %s
                """,
                (product_id,)
            )

            cur.execute(
                """
                DELETE FROM order_items
                WHERE product_id = %s
                AND order_id IN (
                    SELECT id
                    FROM orders
                    WHERE delivery_status = 'Cancelled'
                )
                """,
                (product_id,)
            )

            cur.execute(
                """
                DELETE FROM marketplace_products
                WHERE id = %s
                  AND farmer_id = %s
                """,
                (
                    product_id,
                    session["user_id"]
                )
            )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Product deleted successfully."
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "DELETE PRODUCT ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete product."
        }), 500

    finally:

        if conn:
            conn.close()


# =========================================================
# PRODUCT STATUS
# =========================================================

@marketplace_bp.route(
    "/farmer/products/status/<int:product_id>",
    methods=["POST"]
)
def product_status(product_id):

    if not farmer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = None

    try:

        conn = get_db()

        product = execute_fetchone(
            conn,
            """
            SELECT status, quantity
            FROM marketplace_products
            WHERE id = %s
              AND farmer_id = %s
            """,
            (
                product_id,
                session["user_id"]
            )
        )

        product = row_to_dict(
            product
        )

        if not product:

            return jsonify({
                "success": False,
                "message": "Product not found."
            }), 404

        new_status = request.form.get(
            "status",
            ""
        ).strip().lower()

        if new_status not in (
            "active",
            "inactive"
        ):

            current = str(
                product.get("status")
                or "active"
            ).lower()

            new_status = (
                "inactive"
                if current == "active"
                else "active"
            )

        if (
            new_status == "active"
            and
            float(
                product.get("quantity", 0)
                or 0
            ) <= 0
        ):

            return jsonify({
                "success": False,
                "message": "Add stock before activating product."
            }), 400

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE marketplace_products
                SET
                    status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND farmer_id = %s
                """,
                (
                    new_status,
                    product_id,
                    session["user_id"]
                )
            )

        conn.commit()

        return jsonify({
            "success": True,
            "status": new_status
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "PRODUCT STATUS ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to update status."
        }), 500

    finally:

        if conn:
            conn.close()


# =========================================================
# CONSUMER MARKETPLACE
# =========================================================

@marketplace_bp.route(
    "/consumer/marketplace"
)
def consumer_marketplace():

    if not consumer_only():
        return login_redirect()

    search = request.args.get(
        "search",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()

    conn = None

    try:

        conn = get_db()

        query = """
            SELECT
                p.*,
                u.name AS farmer_name
            FROM marketplace_products p
            LEFT JOIN users u
                ON p.farmer_id = u.id
            WHERE LOWER(
                COALESCE(
                    p.status,
                    'active'
                )
            ) = 'active'
            AND p.quantity > 0
        """

        params = []

        if search:

            query += """
                AND (
                    LOWER(
                        p.product_name
                    ) LIKE %s

                    OR

                    LOWER(
                        COALESCE(
                            p.description,
                            ''
                        )
                    ) LIKE %s

                    OR

                    LOWER(
                        COALESCE(
                            p.category,
                            ''
                        )
                    ) LIKE %s
                )
            """

            keyword = (
                "%"
                + search.lower()
                + "%"
            )

            params.extend([
                keyword,
                keyword,
                keyword
            ])

        if category:

            query += """
                AND LOWER(
                    COALESCE(
                        p.category,
                        ''
                    )
                ) = LOWER(%s)
            """

            params.append(
                category
            )

        query += """
            ORDER BY
                p.created_at DESC,
                p.id DESC
        """

        products = execute_fetchall(
            conn,
            query,
            params
        )

        products = rows_to_dict(
            products
        )

        for product in products:

            product.update(
                get_product_intelligence(
                    product
                )
            )

        categories = execute_fetchall(
            conn,
            """
            SELECT DISTINCT category
            FROM marketplace_products
            WHERE category IS NOT NULL
              AND TRIM(category) <> ''
            ORDER BY category
            """
        )

        categories = rows_to_dict(
            categories
        )

        return render_template(
            "consumer_marketplace.html",
            products=products,
            categories=categories,
            search=search,
            selected_category=category
        )

    except Exception as e:

        print(
            "CONSUMER MARKETPLACE ERROR:",
            repr(e)
        )

        return render_template(
            "consumer_marketplace.html",
            products=[],
            categories=[],
            search=search,
            selected_category=category
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# PRODUCT DETAILS
# =========================================================

@marketplace_bp.route(
    "/consumer/product/<int:product_id>"
)
def product_details(product_id):

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        product = execute_fetchone(
            conn,
            """
            SELECT
                p.*,
                u.name AS farmer_name,
                u.mobile AS farmer_mobile
            FROM marketplace_products p
            LEFT JOIN users u
                ON p.farmer_id = u.id
            WHERE p.id = %s
            """,
            (
                product_id,
            )
        )

        product = row_to_dict(
            product
        )

        if not product:

            flash(
                "Product not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "marketplace.consumer_marketplace"
                )
            )

        product.update(
            get_product_intelligence(
                product
            )
        )

        return render_template(
            "product_details.html",
            product=product
        )

    except Exception as e:

        print(
            "PRODUCT DETAILS ERROR:",
            repr(e)
        )

        flash(
            "Unable to open product.",
            "danger"
        )

        return redirect(
            url_for(
                "marketplace.consumer_marketplace"
            )
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# ADD TO CART
# =========================================================

@marketplace_bp.route(
    "/consumer/cart/add",
    methods=["POST"]
)
def add_to_cart():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Please login as Consumer."
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    try:

        product_id = int(
            data.get(
                "product_id"
            )
        )

    except Exception:

        return jsonify({
            "success": False,
            "message": "Invalid product."
        }), 400

    try:

        quantity = float(
            data.get(
                "quantity",
                1
            )
        )

    except Exception:

        quantity = 1

    if quantity <= 0:
        quantity = 1

    conn = None

    try:

        conn = get_db()

        product = execute_fetchone(
            conn,
            """
            SELECT *
            FROM marketplace_products
            WHERE id = %s
              AND LOWER(
                    COALESCE(
                        status,
                        'active'
                    )
                  ) = 'active'
              AND quantity > 0
            """,
            (
                product_id,
            )
        )

        product = row_to_dict(
            product
        )

        if not product:

            return jsonify({
                "success": False,
                "message": "Product unavailable."
            }), 404

        stock = float(
            product.get("quantity", 0)
            or 0
        )

        existing = execute_fetchone(
            conn,
            """
            SELECT *
            FROM cart
            WHERE user_id = %s
              AND product_id = %s
            """,
            (
                session["user_id"],
                product_id
            )
        )

        existing = row_to_dict(
            existing
        )

        if existing:

            new_quantity = (
                float(
                    existing.get(
                        "quantity",
                        0
                    )
                    or 0
                )
                + quantity
            )

            if new_quantity > stock:

                return jsonify({
                    "success": False,
                    "message": "Not enough stock."
                }), 400

            with conn.cursor() as cur:

                cur.execute(
                    """
                    UPDATE cart
                    SET quantity = %s
                    WHERE id = %s
                    """,
                    (
                        new_quantity,
                        existing["id"]
                    )
                )

        else:

            if quantity > stock:

                return jsonify({
                    "success": False,
                    "message": "Not enough stock."
                }), 400

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO cart
                    (
                        user_id,
                        product_id,
                        quantity
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        session["user_id"],
                        product_id,
                        quantity
                    )
                )

        conn.commit()

        count_row = execute_fetchone(
            conn,
            """
            SELECT COALESCE(
                SUM(quantity),
                0
            ) AS count
            FROM cart
            WHERE user_id = %s
            """,
            (
                session["user_id"],
            )
        )

        count_row = row_to_dict(
            count_row
        )

        return jsonify({
            "success": True,
            "message": "Product added to cart.",
            "cart_count": float(
                count_row.get("count", 0)
                or 0
            )
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "ADD CART ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to add product to cart."
        }), 500

    finally:

        if conn:
            conn.close()


# =========================================================
# CART
# =========================================================

@marketplace_bp.route(
    "/consumer/cart"
)
def cart():

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        cart_items = execute_fetchall(
            conn,
            """
            SELECT
                c.id AS cart_id,
                c.quantity AS cart_quantity,

                p.id,
                p.product_name,
                p.category,
                p.description,
                p.price,
                p.quantity,
                p.unit,
                p.image,
                p.status,
                p.farmer_id,

                u.name AS farmer_name

            FROM cart c

            JOIN marketplace_products p
                ON c.product_id = p.id

            LEFT JOIN users u
                ON p.farmer_id = u.id

            WHERE c.user_id = %s

            ORDER BY c.id DESC
            """,
            (
                session["user_id"],
            )
        )

        cart_items = rows_to_dict(
            cart_items
        )

        subtotal = 0

        for item in cart_items:

            subtotal += (
                float(
                    item.get(
                        "price",
                        0
                    )
                    or 0
                )
                *
                float(
                    item.get(
                        "cart_quantity",
                        0
                    )
                    or 0
                )
            )

        return render_template(
            "cart.html",
            cart=cart_items,
            subtotal=subtotal,
            total=subtotal
        )

    except Exception as e:

        print(
            "CART ERROR:",
            repr(e)
        )

        return render_template(
            "cart.html",
            cart=[],
            subtotal=0,
            total=0
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# UPDATE CART
# =========================================================

@marketplace_bp.route(
    "/consumer/cart/update",
    methods=["POST"]
)
def update_cart():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    try:

        cart_id = int(
            data.get(
                "cart_id"
            )
        )

        quantity = float(
            data.get(
                "quantity"
            )
        )

    except Exception:

        return jsonify({
            "success": False,
            "message": "Invalid cart data."
        }), 400

    if quantity <= 0:
        return remove_cart_item_internal(
            cart_id
        )

    conn = None

    try:

        conn = get_db()

        item = execute_fetchone(
            conn,
            """
            SELECT
                c.id,
                c.product_id,
                p.quantity AS stock,
                p.status
            FROM cart c
            JOIN marketplace_products p
                ON c.product_id = p.id
            WHERE c.id = %s
              AND c.user_id = %s
            """,
            (
                cart_id,
                session["user_id"]
            )
        )

        item = row_to_dict(
            item
        )

        if not item:

            return jsonify({
                "success": False,
                "message": "Cart item not found."
            }), 404

        stock = float(
            item.get("stock", 0)
            or 0
        )

        if quantity > stock:

            return jsonify({
                "success": False,
                "message": (
                    f"Only {stock:g} available."
                )
            }), 400

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE cart
                SET quantity = %s
                WHERE id = %s
                  AND user_id = %s
                """,
                (
                    quantity,
                    cart_id,
                    session["user_id"]
                )
            )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Cart updated."
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "UPDATE CART ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to update cart."
        }), 500

    finally:

        if conn:
            conn.close()


# =========================================================
# REMOVE CART INTERNAL
# =========================================================

def remove_cart_item_internal(
    cart_id
):

    conn = None

    try:

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                DELETE FROM cart
                WHERE id = %s
                  AND user_id = %s
                """,
                (
                    cart_id,
                    session["user_id"]
                )
            )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Item removed from cart."
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "REMOVE CART ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to remove item."
        }), 500

    finally:

        if conn:
            conn.close()


# =========================================================
# REMOVE CART
# =========================================================

@marketplace_bp.route(
    "/consumer/cart/remove",
    methods=["POST"]
)
def remove_from_cart():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    try:

        cart_id = int(
            data.get(
                "cart_id"
            )
        )

    except Exception:

        return jsonify({
            "success": False,
            "message": "Invalid cart item."
        }), 400

    return remove_cart_item_internal(
        cart_id
    )


# =========================================================
# CLEAR CART
# =========================================================

@marketplace_bp.route(
    "/consumer/cart/clear",
    methods=["POST"]
)
def clear_cart():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = None

    try:

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                DELETE FROM cart
                WHERE user_id = %s
                """,
                (
                    session["user_id"],
                )
            )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Cart cleared."
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "CLEAR CART ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to clear cart."
        }), 500

    finally:

        if conn:
            conn.close()


# =========================================================
# ADD WISHLIST
# =========================================================

@marketplace_bp.route(
    "/consumer/wishlist/add",
    methods=["POST"]
)
def add_to_wishlist():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    try:

        product_id = int(
            data.get(
                "product_id"
            )
        )

    except Exception:

        return jsonify({
            "success": False,
            "message": "Invalid product."
        }), 400

    conn = None

    try:

        conn = get_db()

        product = execute_fetchone(
            conn,
            """
            SELECT id
            FROM marketplace_products
            WHERE id = %s
            """,
            (
                product_id,
            )
        )

        if not product:

            return jsonify({
                "success": False,
                "message": "Product not found."
            }), 404

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO wishlist
                (
                    user_id,
                    product_id
                )
                VALUES
                (
                    %s,
                    %s
                )
                ON CONFLICT
                (
                    user_id,
                    product_id
                )
                DO NOTHING
                """,
                (
                    session["user_id"],
                    product_id
                )
            )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Added to wishlist."
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "WISHLIST ADD ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to add to wishlist."
        }), 500

    finally:

        if conn:
            conn.close()


# =========================================================
# WISHLIST
# =========================================================

@marketplace_bp.route(
    "/consumer/wishlist"
)
def wishlist():

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        items = execute_fetchall(
            conn,
            """
            SELECT
                w.id,
                w.product_id,

                p.product_name AS name,
                p.product_name,
                p.description,
                p.price,
                p.quantity,
                p.unit,
                p.image,
                p.category,
                p.status

            FROM wishlist w

            JOIN marketplace_products p
                ON w.product_id = p.id

            WHERE w.user_id = %s

            ORDER BY w.id DESC
            """,
            (
                session["user_id"],
            )
        )

        items = rows_to_dict(
            items
        )

        return render_template(
            "wishlist.html",
            wishlist=items,
            items=items
        )

    except Exception as e:

        print(
            "WISHLIST ERROR:",
            repr(e)
        )

        return render_template(
            "wishlist.html",
            wishlist=[],
            items=[]
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# REMOVE WISHLIST
# =========================================================

@marketplace_bp.route(
    "/consumer/wishlist/remove",
    methods=["POST"]
)
def remove_from_wishlist():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    try:

        wishlist_id = int(
            data.get(
                "wishlist_id",
                data.get("id")
            )
        )

    except Exception:

        return jsonify({
            "success": False,
            "message": "Invalid wishlist item."
        }), 400

    conn = None

    try:

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                DELETE FROM wishlist
                WHERE id = %s
                  AND user_id = %s
                """,
                (
                    wishlist_id,
                    session["user_id"]
                )
            )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Removed from wishlist."
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "REMOVE WISHLIST ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to remove wishlist item."
        }), 500

    finally:

        if conn:
            conn.close()


# =========================================================
# CHECKOUT
# =========================================================

@marketplace_bp.route(
    "/consumer/checkout",
    methods=["GET", "POST"]
)
def checkout():

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        cart_items = execute_fetchall(
            conn,
            """
            SELECT
                c.id AS cart_id,
                c.product_id,
                c.quantity AS cart_quantity,

                p.product_name,
                p.description,
                p.price,
                p.quantity,
                p.unit,
                p.image,
                p.farmer_id,
                p.status

            FROM cart c

            JOIN marketplace_products p
                ON c.product_id = p.id

            WHERE c.user_id = %s

            ORDER BY c.id DESC
            """,
            (
                session["user_id"],
            )
        )

        cart_items = rows_to_dict(
            cart_items
        )

        total = 0

        for item in cart_items:

            total += (
                float(
                    item.get(
                        "price",
                        0
                    )
                    or 0
                )
                *
                float(
                    item.get(
                        "cart_quantity",
                        0
                    )
                    or 0
                )
            )

        # -------------------------------------------------
        # GET
        # -------------------------------------------------

        if request.method == "GET":

            return render_template(
                "checkout.html",
                cart=cart_items,
                total=total,
                buy_now_product=None
            )

        # -------------------------------------------------
        # EMPTY CART
        # -------------------------------------------------

        if not cart_items:

            flash(
                "Your cart is empty.",
                "warning"
            )

            return redirect(
                url_for(
                    "marketplace.consumer_marketplace"
                )
            )

        delivery_address = request.form.get(
            "delivery_address",
            ""
        ).strip()

        city = request.form.get(
            "city",
            ""
        ).strip()

        pincode = request.form.get(
            "pin",
            request.form.get(
                "pincode",
                ""
            )
        ).strip()

        payment_method = request.form.get(
            "payment_method",
            "Cash on Delivery"
        ).strip()

        if not delivery_address:

            flash(
                "Delivery address is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "marketplace.checkout"
                )
            )

        if not city:

            flash(
                "City is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "marketplace.checkout"
                )
            )

        if (
            not pincode.isdigit()
            or len(pincode) != 6
        ):

            flash(
                "Please enter a valid 6 digit PIN code.",
                "danger"
            )

            return redirect(
                url_for(
                    "marketplace.checkout"
                )
            )

        if payment_method not in (
            "Cash on Delivery",
            "Online Payment"
        ):

            payment_method = (
                "Cash on Delivery"
            )

        if payment_method == "Online Payment":

            flash(
                "Online Payment is coming soon. "
                "Cash on Delivery selected.",
                "warning"
            )

            payment_method = (
                "Cash on Delivery"
            )

        # -------------------------------------------------
        # GROUP BY FARMER
        # -------------------------------------------------

        farmer_groups = {}

        for item in cart_items:

            farmer_id = item.get(
                "farmer_id"
            )

            if not farmer_id:

                raise ValueError(
                    "Farmer information is missing."
                )

            requested = float(
                item.get(
                    "cart_quantity",
                    0
                )
                or 0
            )

            stock = float(
                item.get(
                    "quantity",
                    0
                )
                or 0
            )

            status = str(
                item.get(
                    "status",
                    "active"
                )
                or "active"
            ).lower()

            if status != "active":

                raise ValueError(
                    f"{item['product_name']} "
                    "is not available."
                )

            if requested <= 0:

                raise ValueError(
                    "Invalid cart quantity."
                )

            if requested > stock:

                raise ValueError(
                    f"Insufficient stock for "
                    f"{item['product_name']}."
                )

            farmer_groups.setdefault(
                int(farmer_id),
                []
            ).append(item)

        created_orders = []

        # -------------------------------------------------
        # CREATE ORDERS
        # -------------------------------------------------

        for farmer_id, items in farmer_groups.items():

            farmer_total = 0

            for item in items:

                farmer_total += (
                    float(
                        item.get(
                            "cart_quantity",
                            0
                        )
                        or 0
                    )
                    *
                    float(
                        item.get(
                            "price",
                            0
                        )
                        or 0
                    )
                )

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO orders
                    (
                        buyer_id,
                        farmer_id,
                        total_amount,
                        delivery_status,
                        delivery_address,
                        city,
                        pincode,
                        payment_method
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        'Pending',
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        session["user_id"],
                        farmer_id,
                        farmer_total,
                        delivery_address,
                        city,
                        pincode,
                        payment_method
                    )
                )

                order_id = cur.fetchone()["id"]

                created_orders.append(
                    order_id
                )

                for item in items:

                    quantity = float(
                        item.get(
                            "cart_quantity",
                            0
                        )
                        or 0
                    )

                    price = float(
                        item.get(
                            "price",
                            0
                        )
                        or 0
                    )

                    item_total = (
                        quantity * price
                    )

                    # Stock-safe update
                    cur.execute(
                        """
                        UPDATE marketplace_products
                        SET
                            quantity =
                                quantity - %s,
                            status =
                                CASE
                                    WHEN quantity - %s <= 0
                                    THEN 'inactive'
                                    ELSE status
                                END,
                            updated_at =
                                CURRENT_TIMESTAMP
                        WHERE id = %s
                          AND quantity >= %s
                        """,
                        (
                            quantity,
                            quantity,
                            item["product_id"],
                            quantity
                        )
                    )

                    if cur.rowcount != 1:

                        raise ValueError(
                            f"Stock changed for "
                            f"{item['product_name']}. "
                            "Please try again."
                        )

                    cur.execute(
                        """
                        INSERT INTO order_items
                        (
                            order_id,
                            product_id,
                            quantity,
                            price,
                            total_amount
                        )
                        VALUES
                        (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                        """,
                        (
                            order_id,
                            item["product_id"],
                            quantity,
                            price,
                            item_total
                        )
                    )

        # -------------------------------------------------
        # CLEAR CART
        # -------------------------------------------------

        with conn.cursor() as cur:

            cur.execute(
                """
                DELETE FROM cart
                WHERE user_id = %s
                """,
                (
                    session["user_id"],
                )
            )

        conn.commit()

        flash(
            "Order placed successfully!",
            "success"
        )

        return redirect(
            url_for(
                "marketplace.consumer_orders"
            )
        )

    except Exception as e:
        if conn:
            conn.rollback()

        import traceback

        print("=" * 60)
        print("CHECKOUT ERROR")
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", repr(e))
        traceback.print_exc()
        print("=" * 60)

        flash(
            f"Unable to place order: {type(e).__name__}: {str(e)}",
            "danger"
        )

        return redirect(
            url_for("marketplace.checkout")
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# BUY NOW
# =========================================================

@marketplace_bp.route(
    "/consumer/buy-now/<int:product_id>",
    methods=["POST"]
)
def buy_now(product_id):

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        product = execute_fetchone(
            conn,
            """
            SELECT *
            FROM marketplace_products
            WHERE id = %s
              AND LOWER(
                    COALESCE(
                        status,
                        'active'
                    )
                  ) = 'active'
              AND quantity > 0
            """,
            (
                product_id,
            )
        )

        product = row_to_dict(
            product
        )

        if not product:

            flash(
                "Product not found or out of stock.",
                "danger"
            )

            return redirect(
                url_for(
                    "marketplace.consumer_marketplace"
                )
            )

        return render_template(
            "checkout.html",
            buy_now_product=product,
            cart=[],
            total=float(
                product.get(
                    "price",
                    0
                )
                or 0
            )
        )

    except Exception as e:

        print(
            "BUY NOW ERROR:",
            repr(e)
        )

        flash(
            "Unable to process Buy Now.",
            "danger"
        )

        return redirect(
            url_for(
                "marketplace.consumer_marketplace"
            )
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# PLACE BUY NOW ORDER
# =========================================================

@marketplace_bp.route(
    "/consumer/order/place/<int:product_id>",
    methods=["POST"]
)
def place_order(product_id):

    if not consumer_only():
        return login_redirect()

    conn = None

    try:
        conn = get_db()

        # -------------------------------------------------
        # GET PRODUCT + FARMER
        # -------------------------------------------------
        product = execute_fetchone(
            conn,
            """
            SELECT
                id,
                farmer_id,
                product_name,
                price,
                quantity,
                unit,
                image,
                status
            FROM marketplace_products
            WHERE id = %s
            FOR UPDATE
            """,
            (product_id,)
        )

        product = row_to_dict(product)

        if not product:
            flash("Product not found.", "danger")
            return redirect(
                url_for("marketplace.consumer_marketplace")
            )

        farmer_id = product.get("farmer_id")

        if not farmer_id:
            flash("Farmer information is missing for this product.", "danger")
            return redirect(
                url_for("marketplace.consumer_marketplace")
            )

        # -------------------------------------------------
        # QUANTITY
        # -------------------------------------------------
        try:
            qty = float(request.form.get("quantity", 1))
        except (TypeError, ValueError):
            qty = 1

        if qty <= 0:
            qty = 1

        stock = float(product.get("quantity") or 0)
        status = str(product.get("status") or "active").lower()

        if status != "active" or stock < qty:
            flash(
                f"Only {stock:g} {product.get('unit', 'items')} "
                f"of {product.get('product_name', 'this product')} are available.",
                "danger"
            )
            return redirect(
                url_for(
                    "marketplace.buy_now",
                    product_id=product_id
                )
            )

        # -------------------------------------------------
        # DELIVERY DETAILS
        # -------------------------------------------------
        address = request.form.get("delivery_address", "").strip()
        city = request.form.get("city", "").strip()
        pincode = request.form.get(
            "pincode",
            request.form.get("pin", "")
        ).strip()

        payment_method = request.form.get(
            "payment_method",
            "Cash on Delivery"
        ).strip()

        if not address:
            flash("Delivery address is required.", "danger")
            return redirect(
                url_for("marketplace.buy_now", product_id=product_id)
            )

        if not city:
            flash("City is required.", "danger")
            return redirect(
                url_for("marketplace.buy_now", product_id=product_id)
            )

        if not pincode.isdigit() or len(pincode) != 6:
            flash("Please enter a valid 6 digit PIN code.", "danger")
            return redirect(
                url_for("marketplace.buy_now", product_id=product_id)
            )

        if payment_method not in (
            "Cash on Delivery",
            "Online Payment"
        ):
            payment_method = "Cash on Delivery"

        if payment_method == "Online Payment":
            payment_method = "Cash on Delivery"

        price = float(product.get("price") or 0)
        total = price * qty

        # -------------------------------------------------
        # CREATE ORDER + ITEM + REDUCE STOCK
        # ALL IN ONE TRANSACTION
        # -------------------------------------------------
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE marketplace_products
                SET
                    quantity = quantity - %s,
                    status = CASE
                        WHEN quantity - %s <= 0
                        THEN 'inactive'
                        ELSE status
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND farmer_id = %s
                  AND quantity >= %s
                  AND LOWER(COALESCE(status, 'active')) = 'active'
                """,
                (
                    qty,
                    qty,
                    product_id,
                    farmer_id,
                    qty
                )
            )

            if cur.rowcount != 1:
                raise ValueError(
                    "Product stock changed or the product is no longer available."
                )

            cur.execute(
                """
                INSERT INTO orders
                (
                    buyer_id,
                    farmer_id,
                    product_id,
                    quantity,
                    price,
                    total_amount,
                    delivery_status,
                    delivery_address,
                    city,
                    pincode,
                    payment_method,
                    payment_status
                )
                VALUES
                (
                    %s, %s, %s, %s, %s, %s,
                    'Pending',
                    %s, %s, %s, %s,
                    'Pending'
                )
                RETURNING id
                """,
                (
                    session["user_id"],
                    farmer_id,
                    product_id,
                    qty,
                    price,
                    total,
                    address,
                    city,
                    pincode,
                    payment_method
                )
            )

            order_row = cur.fetchone()
            order_id = order_row["id"]

            cur.execute(
                """
                INSERT INTO order_items
                (
                    order_id,
                    product_id,
                    farmer_id,
                    product_name,
                    quantity,
                    price,
                    total_amount
                )
                VALUES
                (
                    %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    order_id,
                    product_id,
                    farmer_id,
                    product.get("product_name"),
                    qty,
                    price,
                    total
                )
            )

        conn.commit()

        flash(
            f"Order #{order_id} placed successfully!",
            "success"
        )

        return redirect(
            url_for("marketplace.consumer_orders")
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "PLACE ORDER ERROR:",
            repr(e)
        )

        flash(
            f"Unable to place order: {str(e)}",
            "danger"
        )

        return redirect(
            url_for("marketplace.consumer_marketplace")
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# CONSUMER ORDERS
# =========================================================

@marketplace_bp.route(
    "/consumer/orders"
)
def consumer_orders():

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        orders = execute_fetchall(
            conn,
            """
            SELECT
                o.id,
                o.buyer_id,
                o.farmer_id,
                o.total_amount,
                o.delivery_status AS status,
                o.delivery_address,
                o.city,
                o.pincode,
                COALESCE(
                    o.payment_method,
                    'Cash on Delivery'
                ) AS payment_method,
                o.created_at,

                u.name AS farmer_name,
                u.mobile AS farmer_mobile

            FROM orders o

            LEFT JOIN users u
                ON o.farmer_id = u.id

            WHERE o.buyer_id = %s

            ORDER BY o.id DESC
            """,
            (
                session["user_id"],
            )
        )

        orders = rows_to_dict(
            orders
        )

        order_list = []

        for order in orders:

            items = execute_fetchall(
                conn,
                """
                SELECT
                    oi.id,
                    oi.product_id,
                    oi.quantity,
                    oi.price,
                    oi.total_amount AS total,

                    p.product_name,
                    p.image,
                    p.category,
                    p.unit

                FROM order_items oi

                LEFT JOIN marketplace_products p
                    ON p.id = oi.product_id

                WHERE oi.order_id = %s

                ORDER BY oi.id ASC
                """,
                (
                    order["id"],
                )
            )

            order["items"] = rows_to_dict(
                items
            )

            order_list.append(
                order
            )

        return render_template(
            "consumer_orders.html",
            orders=order_list
        )

    except Exception as e:

        print(
            "CONSUMER ORDERS ERROR:",
            repr(e)
        )

        return render_template(
            "consumer_orders.html",
            orders=[]
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# CONSUMER ORDER DETAILS
# =========================================================

@marketplace_bp.route(
    "/consumer/order/<int:order_id>"
)
def consumer_order_details(order_id):

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        order = execute_fetchone(
            conn,
            """
            SELECT
                o.*,
                o.delivery_status AS status,

                COALESCE(
                    o.payment_method,
                    'Cash on Delivery'
                ) AS payment_method,

                u.name AS farmer_name,
                u.mobile AS farmer_mobile

            FROM orders o

            LEFT JOIN users u
                ON o.farmer_id = u.id

            WHERE o.id = %s
              AND o.buyer_id = %s
            """,
            (
                order_id,
                session["user_id"]
            )
        )

        order = row_to_dict(
            order
        )

        if not order:

            flash(
                "Order not found.",
                "error"
            )

            return redirect(
                url_for(
                    "marketplace.consumer_orders"
                )
            )

        items = execute_fetchall(
            conn,
            """
            SELECT
                oi.id,
                oi.product_id,
                oi.quantity,
                oi.price,
                oi.total_amount AS total,

                p.product_name,
                p.category,
                p.image,
                p.unit

            FROM order_items oi

            LEFT JOIN marketplace_products p
                ON p.id = oi.product_id

            WHERE oi.order_id = %s

            ORDER BY oi.id ASC
            """,
            (
                order_id,
            )
        )

        return render_template(
            "consumer_order_details.html",
            order=order,
            items=rows_to_dict(
                items
            )
        )

    except Exception as e:

        print(
            "ORDER DETAILS ERROR:",
            repr(e)
        )

        flash(
            "Unable to open order.",
            "error"
        )

        return redirect(
            url_for(
                "marketplace.consumer_orders"
            )
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# EDIT CONSUMER ORDER
# =========================================================

@marketplace_bp.route(
    "/consumer/order/<int:order_id>/edit",
    methods=["GET", "POST"]
)
def edit_consumer_order(order_id):

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        order = execute_fetchone(
            conn,
            """
            SELECT
                o.*,
                o.delivery_status AS status,

                COALESCE(
                    o.payment_method,
                    'Cash on Delivery'
                ) AS payment_method

            FROM orders o

            WHERE o.id = %s
              AND o.buyer_id = %s
            """,
            (
                order_id,
                session["user_id"]
            )
        )

        order = row_to_dict(
            order
        )

        if not order:

            flash(
                "Order not found.",
                "error"
            )

            return redirect(
                url_for(
                    "marketplace.consumer_orders"
                )
            )

        current_status = str(
            order.get(
                "status",
                "Pending"
            )
            or "Pending"
        ).lower()

        editable_statuses = [
            "pending",
            "placed",
            "confirmed"
        ]

        if current_status not in editable_statuses:

            flash(
                "This order can no longer be edited.",
                "warning"
            )

            return redirect(
                url_for(
                    "marketplace.consumer_order_details",
                    order_id=order_id
                )
            )

        if request.method == "POST":

            delivery_address = request.form.get(
                "delivery_address",
                ""
            ).strip()

            city = request.form.get(
                "city",
                ""
            ).strip()

            pincode = request.form.get(
                "pincode",
                request.form.get(
                    "pin",
                    ""
                )
            ).strip()

            payment_method = request.form.get(
                "payment_method",
                "Cash on Delivery"
            ).strip()

            if not delivery_address:

                flash(
                    "Delivery address is required.",
                    "error"
                )

                return render_template(
                    "edit_order.html",
                    order=order
                )

            if not city:

                flash(
                    "City is required.",
                    "error"
                )

                return render_template(
                    "edit_order.html",
                    order=order
                )

            if (
                not pincode.isdigit()
                or len(pincode) != 6
            ):

                flash(
                    "Please enter a valid 6 digit PIN code.",
                    "error"
                )

                return render_template(
                    "edit_order.html",
                    order=order
                )

            if payment_method not in (
                "Cash on Delivery",
                "Online Payment"
            ):

                payment_method = (
                    "Cash on Delivery"
                )

            if payment_method == "Online Payment":

                payment_method = (
                    "Cash on Delivery"
                )

            with conn.cursor() as cur:

                cur.execute(
                    """
                    UPDATE orders
                    SET
                        delivery_address = %s,
                        city = %s,
                        pincode = %s,
                        payment_method = %s,
                        updated_at =
                            CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND buyer_id = %s
                    """,
                    (
                        delivery_address,
                        city,
                        pincode,
                        payment_method,
                        order_id,
                        session["user_id"]
                    )
                )

            conn.commit()

            flash(
                "Order details updated successfully!",
                "success"
            )

            return redirect(
                url_for(
                    "marketplace.consumer_order_details",
                    order_id=order_id
                )
            )

        return render_template(
            "edit_order.html",
            order=order
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "EDIT ORDER ERROR:",
            repr(e)
        )

        flash(
            "Unable to update order.",
            "error"
        )

        return redirect(
            url_for(
                "marketplace.consumer_orders"
            )
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# CANCEL CONSUMER ORDER
# =========================================================

@marketplace_bp.route(
    "/consumer/order/<int:order_id>/cancel",
    methods=["POST"]
)
def cancel_consumer_order(order_id):

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        order = execute_fetchone(
            conn,
            """
            SELECT
                id,
                delivery_status AS status
            FROM orders
            WHERE id = %s
              AND buyer_id = %s
            FOR UPDATE
            """,
            (
                order_id,
                session["user_id"]
            )
        )

        order = row_to_dict(
            order
        )

        if not order:

            flash(
                "Order not found.",
                "error"
            )

            return redirect(
                url_for(
                    "marketplace.consumer_orders"
                )
            )

        current_status = str(
            order.get(
                "status",
                "Pending"
            )
            or "Pending"
        ).lower()

        cancellable_statuses = [
            "pending",
            "placed",
            "confirmed"
        ]

        if current_status not in cancellable_statuses:

            flash(
                "This order cannot be cancelled now.",
                "warning"
            )

            return redirect(
                url_for(
                    "marketplace.consumer_order_details",
                    order_id=order_id
                )
            )

        items = execute_fetchall(
            conn,
            """
            SELECT
                product_id,
                quantity
            FROM order_items
            WHERE order_id = %s
            """,
            (
                order_id,
            )
        )

        with conn.cursor() as cur:

            for item in items:

                item = row_to_dict(
                    item
                )

                cur.execute(
                    """
                    UPDATE marketplace_products
                    SET
                        quantity =
                            quantity + %s,
                        status = 'active',
                        updated_at =
                            CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        float(
                            item.get(
                                "quantity",
                                0
                            )
                            or 0
                        ),
                        item["product_id"]
                    )
                )

            cur.execute(
                """
                UPDATE orders
                SET
                    delivery_status = 'Cancelled',
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE id = %s
                  AND buyer_id = %s
                """,
                (
                    order_id,
                    session["user_id"]
                )
            )

        conn.commit()

        flash(
            f"Order #{order_id} cancelled successfully.",
            "success"
        )

        return redirect(
            url_for(
                "marketplace.consumer_orders"
            )
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "CANCEL ORDER ERROR:",
            repr(e)
        )

        flash(
            "Unable to cancel order.",
            "error"
        )

        return redirect(
            url_for(
                "marketplace.consumer_orders"
            )
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# FARMER ORDERS
# =========================================================

@marketplace_bp.route("/orders")
def farmer_orders():

    if not farmer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        orders = execute_fetchall(
            conn,
            """
            SELECT
                o.id,
                o.buyer_id,
                o.farmer_id,
                o.total_amount,
                o.delivery_status AS status,
                o.delivery_address,
                o.city,
                o.pincode,
                o.payment_method,
                o.created_at,

                u.name AS consumer_name,
                u.mobile AS consumer_mobile,
                u.email AS consumer_email

            FROM orders o

            LEFT JOIN users u
                ON o.buyer_id = u.id

            WHERE o.farmer_id = %s

            ORDER BY o.id DESC
            """,
            (
                session["user_id"],
            )
        )

        orders = rows_to_dict(
            orders
        )

        order_items = {}

        for order in orders:

            items = execute_fetchall(
                conn,
                """
                SELECT
                    oi.id,
                    oi.order_id,
                    oi.product_id,
                    oi.quantity,
                    oi.price,
                    oi.total_amount AS total,

                    p.product_name,
                    p.image,
                    p.unit

                FROM order_items oi

                LEFT JOIN marketplace_products p
                    ON oi.product_id = p.id

                WHERE oi.order_id = %s

                ORDER BY oi.id ASC
                """,
                (
                    order["id"],
                )
            )

            order_items[
                order["id"]
            ] = rows_to_dict(
                items
            )

        return render_template(
            "farmer_orders.html",
            orders=orders,
            order_items=order_items
        )

    except Exception as e:

        print(
            "FARMER ORDERS ERROR:",
            repr(e)
        )

        return render_template(
            "farmer_orders.html",
            orders=[],
            order_items={}
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# FARMER UPDATE ORDER STATUS
# =========================================================

@marketplace_bp.route(
    "/farmer/orders/update/<int:order_id>",
    methods=["POST"]
)
def update_order_status(order_id):

    if not farmer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    status = request.form.get(
        "status",
        ""
    ).strip()

    allowed_statuses = [
        "Pending",
        "Confirmed",
        "Processing",
        "Shipped",
        "Delivered",
        "Cancelled"
    ]

    if status not in allowed_statuses:

        return jsonify({
            "success": False,
            "message": "Invalid status."
        }), 400

    conn = None

    try:

        conn = get_db()

        order = execute_fetchone(
            conn,
            """
            SELECT
                id,
                delivery_status AS status
            FROM orders
            WHERE id = %s
              AND farmer_id = %s
            FOR UPDATE
            """,
            (
                order_id,
                session["user_id"]
            )
        )

        order = row_to_dict(
            order
        )

        if not order:

            return jsonify({
                "success": False,
                "message": "Order not found."
            }), 404

        old_status = str(
            order.get(
                "status",
                "Pending"
            )
            or "Pending"
        ).lower()

        # -------------------------------------------------
        # RESTORE STOCK ONLY ON FIRST CANCELLATION
        # -------------------------------------------------

        if (
            status == "Cancelled"
            and
            old_status != "cancelled"
        ):

            items = execute_fetchall(
                conn,
                """
                SELECT
                    product_id,
                    quantity
                FROM order_items
                WHERE order_id = %s
                """,
                (
                    order_id,
                )
            )

            with conn.cursor() as cur:

                for item in items:

                    item = row_to_dict(
                        item
                    )

                    cur.execute(
                        """
                        UPDATE marketplace_products
                        SET
                            quantity =
                                quantity + %s,
                            status = 'active',
                            updated_at =
                                CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (
                            float(
                                item.get(
                                    "quantity",
                                    0
                                )
                                or 0
                            ),
                            item["product_id"]
                        )
                    )

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE orders
                SET
                    delivery_status = %s,
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE id = %s
                  AND farmer_id = %s
                """,
                (
                    status,
                    order_id,
                    session["user_id"]
                )
            )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Order status updated successfully.",
            "status": status
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "UPDATE ORDER ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to update order."
        }), 500

    finally:

        if conn:
            conn.close()


# =========================================================
# CONSUMER REPORTS
# =========================================================

@marketplace_bp.route(
    "/consumer/reports"
)
def consumer_reports():

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        total_orders = execute_fetchone(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM orders
            WHERE buyer_id = %s
              AND LOWER(
                    COALESCE(
                        delivery_status,
                        ''
                    )
                  ) != 'cancelled'
            """,
            (
                session["user_id"],
            )
        )

        total_orders = int(
            (
                row_to_dict(
                    total_orders
                )
                or {}
            ).get(
                "count",
                0
            )
            or 0
        )

        total_spending = execute_fetchone(
            conn,
            """
            SELECT COALESCE(
                SUM(total_amount),
                0
            ) AS total
            FROM orders
            WHERE buyer_id = %s
              AND LOWER(
                    COALESCE(
                        delivery_status,
                        ''
                    )
                  ) != 'cancelled'
            """,
            (
                session["user_id"],
            )
        )

        total_spending = float(
            (
                row_to_dict(
                    total_spending
                )
                or {}
            ).get(
                "total",
                0
            )
            or 0
        )

        delivered_orders = execute_fetchone(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM orders
            WHERE buyer_id = %s
              AND LOWER(
                    COALESCE(
                        delivery_status,
                        ''
                    )
                  ) = 'delivered'
            """,
            (
                session["user_id"],
            )
        )

        delivered_orders = int(
            (
                row_to_dict(
                    delivered_orders
                )
                or {}
            ).get(
                "count",
                0
            )
            or 0
        )

        pending_orders = execute_fetchone(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM orders
            WHERE buyer_id = %s
              AND LOWER(
                    COALESCE(
                        delivery_status,
                        ''
                    )
                  )
                  IN (
                      'pending',
                      'placed',
                      'confirmed',
                      'processing',
                      'shipped'
                  )
            """,
            (
                session["user_id"],
            )
        )

        pending_orders = int(
            (
                row_to_dict(
                    pending_orders
                )
                or {}
            ).get(
                "count",
                0
            )
            or 0
        )

        cancelled_orders = execute_fetchone(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM orders
            WHERE buyer_id = %s
              AND LOWER(
                    COALESCE(
                        delivery_status,
                        ''
                    )
                  ) = 'cancelled'
            """,
            (
                session["user_id"],
            )
        )

        cancelled_orders = int(
            (
                row_to_dict(
                    cancelled_orders
                )
                or {}
            ).get(
                "count",
                0
            )
            or 0
        )

        products_bought = execute_fetchone(
            conn,
            """
            SELECT COALESCE(
                SUM(oi.quantity),
                0
            ) AS total
            FROM order_items oi
            JOIN orders o
                ON oi.order_id = o.id
            WHERE o.buyer_id = %s
              AND LOWER(
                    COALESCE(
                        o.delivery_status AS status,
                        ''
                    )
                  ) != 'cancelled'
            """,
            (
                session["user_id"],
            )
        )

        products_bought = float(
            (
                row_to_dict(
                    products_bought
                )
                or {}
            ).get(
                "total",
                0
            )
            or 0
        )

        category_report = execute_fetchall(
            conn,
            """
            SELECT
                COALESCE(
                    p.category,
                    'Other'
                ) AS category,

                SUM(
                    oi.quantity
                ) AS quantity,

                SUM(
                    oi.total_amount
                ) AS amount

            FROM order_items oi

            JOIN orders o
                ON oi.order_id = o.id

            LEFT JOIN marketplace_products p
                ON oi.product_id = p.id

            WHERE o.buyer_id = %s
              AND LOWER(
                    COALESCE(
                        o.delivery_status AS status,
                        ''
                    )
                  ) != 'cancelled'

            GROUP BY
                COALESCE(
                    p.category,
                    'Other'
                )

            ORDER BY amount DESC
            """,
            (
                session["user_id"],
            )
        )

        recent_orders = execute_fetchall(
            conn,
            """
            SELECT
                id,
                total_amount,
                delivery_status,
                created_at
            FROM orders
            WHERE buyer_id = %s
            ORDER BY id DESC
            LIMIT 10
            """,
            (
                session["user_id"],
            )
        )

        return render_template(
            "consumer_reports.html",

            total_orders=total_orders,

            total_spending=total_spending,

            delivered_orders=delivered_orders,

            pending_orders=pending_orders,

            cancelled_orders=cancelled_orders,

            products_bought=products_bought,

            category_report=rows_to_dict(
                category_report
            ),

            recent_orders=rows_to_dict(
                recent_orders
            )
        )

    except Exception as e:

        print(
            "CONSUMER REPORTS ERROR:",
            repr(e)
        )

        return render_template(
            "consumer_reports.html",

            total_orders=0,

            total_spending=0,

            delivered_orders=0,

            pending_orders=0,

            cancelled_orders=0,

            products_bought=0,

            category_report=[],

            recent_orders=[]
        )

    finally:

        if conn:
            conn.close()


# =========================================================
# MARKETPLACE API
# =========================================================

@marketplace_bp.route(
    "/api/marketplace/summary"
)
def marketplace_summary():

    if not logged_in():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = None

    try:

        conn = get_db()

        products = execute_fetchone(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM marketplace_products
            WHERE LOWER(
                COALESCE(status, 'active')
            ) = 'active'
            AND quantity > 0
            """
        )

        low_stock = execute_fetchone(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM marketplace_products
            WHERE farmer_id = %s
              AND quantity > 0
              AND quantity <= 5
            """,
            (
                session["user_id"],
            )
        ) if farmer_only() else None

        cart_count = execute_fetchone(
            conn,
            """
            SELECT COALESCE(
                SUM(quantity),
                0
            ) AS count
            FROM cart
            WHERE user_id = %s
            """,
            (
                session["user_id"],
            )
        ) if consumer_only() else None

        return jsonify({
            "success": True,
            "active_products": float(
                (
                    row_to_dict(
                        products
                    )
                    or {}
                ).get(
                    "count",
                    0
                )
                or 0
            ),
            "low_stock": float(
                (
                    row_to_dict(
                        low_stock
                    )
                    or {}
                ).get(
                    "count",
                    0
                )
                or 0
            ) if low_stock else 0,
            "cart_count": float(
                (
                    row_to_dict(
                        cart_count
                    )
                    or {}
                ).get(
                    "count",
                    0
                )
                or 0
            ) if cart_count else 0
        })

    except Exception as e:

        print(
            "MARKETPLACE SUMMARY ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to load marketplace summary."
        }), 500

    finally:

        if conn:
            conn.close()


# =========================================================
# HEALTH
# =========================================================

@marketplace_bp.route(
    "/api/marketplace/health"
)
def marketplace_health():

    conn = None

    try:

        conn = get_db()

        execute_fetchone(
            conn,
            "SELECT 1 AS health"
        )

        return jsonify({
            "success": True,
            "module": "marketplace",
            "database": "postgresql",
            "status": "healthy"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "module": "marketplace",
            "database": "postgresql",
            "status": "unhealthy",
            "error": str(e)
        }), 500

    finally:

        if conn:
            conn.close()


# =========================================================
# END OF MARKETPLACE ROUTES
# =========================================================
