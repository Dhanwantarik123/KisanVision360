# =========================================================
# KISANVISION360+
# AUTH ROUTES
# PostgreSQL / Supabase
# =========================================================

import re

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash,
    jsonify,
    url_for
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database.db import get_db_connection


# =========================================================
# BLUEPRINT
# =========================================================

auth_bp = Blueprint(
    "auth",
    __name__
)


# =========================================================
# LANGUAGES
# =========================================================

SUPPORTED_LANGUAGES = {
    "en",
    "hi",
    "mr",
    "kn",
    "te",
    "ta",
    "ml",
    "gu",
    "pa",
    "bn",
    "as",
    "or",
    "ur",
    "ne",
    "sa",
    "kok",
    "mai",
    "ks",
    "sd",
    "mni"
}


RTL_LANGUAGES = {
    "ur",
    "ks",
    "sd"
}


# =========================================================
# HELPERS
# =========================================================

def get_language():

    language = session.get(
        "language",
        "en"
    )

    if language not in SUPPORTED_LANGUAGES:

        language = "en"

        session["language"] = language

    return language


def normalize_role(role):

    role = str(
        role or ""
    ).strip().lower()

    if role == "farmer":
        return "farmer"

    if role == "consumer":
        return "consumer"

    if role == "admin":
        return "admin"

    return None


def valid_mobile(mobile):

    return bool(
        re.fullmatch(
            r"[6-9][0-9]{9}",
            mobile
        )
    )


def valid_email(email):

    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email
        )
    )


# =========================================================
# LANGUAGE PAGE
# =========================================================

@auth_bp.route(
    "/language",
    methods=["GET"]
)
def language():

    return render_template(
        "language.html",
        current_language=get_language(),
        supported_languages=SUPPORTED_LANGUAGES
    )


# =========================================================
# SET LANGUAGE
# =========================================================

@auth_bp.route(
    "/set-language",
    methods=["POST"]
)
def set_language():

    data = request.get_json(
        silent=True
    ) or {}

    language = str(
        data.get(
            "language",
            "en"
        )
    ).strip().lower()


    if language not in SUPPORTED_LANGUAGES:

        return jsonify({
            "success": False,
            "message": "Unsupported language"
        }), 400


    session["language"] = language


    return jsonify({
        "success": True,
        "language": language,
        "direction":
            "rtl"
            if language in RTL_LANGUAGES
            else "ltr"
    })


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "GET":

        if session.get("user_id"):

            role = normalize_role(
                session.get("role")
            )

            if role == "farmer":

                return redirect(
                    url_for("farmer.farmer")
                )

            if role == "consumer":

                return redirect(
                    url_for("consumer.consumer")
                )

            if role == "admin":

                return redirect(
                    url_for("admin.admin")
                )


        return render_template(
            "login.html"
        )


    # =====================================================
    # POST LOGIN
    # =====================================================

    login_value = str(
        request.form.get(
            "login",
            ""
        )
    ).strip()


    password = request.form.get(
        "password",
        ""
    )


    remember = (
        request.form.get(
            "remember"
        )
        == "on"
    )


    if not login_value:

        flash(
            "Please enter email or mobile number.",
            "error"
        )

        return render_template(
            "login.html"
        )


    if not password:

        flash(
            "Please enter your password.",
            "error"
        )

        return render_template(
            "login.html"
        )


    connection = None


    try:

        connection = get_db_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                mobile,
                password_hash,
                role,
                preferred_language
            FROM users
            WHERE LOWER(email) = LOWER(%s)
               OR mobile = %s
            LIMIT 1
            """,
            (
                login_value,
                login_value
            )
        )


        user = cursor.fetchone()


        if not user:

            flash(
                "Invalid email/mobile or password.",
                "error"
            )

            return render_template(
                "login.html"
            )


        # RealDictCursor returns dictionary.
        # Normal cursor returns tuple.
        if isinstance(user, dict):

            user_id = user.get("id")

            name = user.get("name")

            email = user.get("email")

            mobile = user.get("mobile")

            password_hash = user.get(
                "password_hash"
            )

            role = user.get("role")

            preferred_language = user.get(
                "preferred_language"
            )

        else:

            (
                user_id,
                name,
                email,
                mobile,
                password_hash,
                role,
                preferred_language
            ) = user


        if not password_hash:

            flash(
                "Account password is not configured.",
                "error"
            )

            return render_template(
                "login.html"
            )


        if not check_password_hash(
            password_hash,
            password
        ):

            flash(
                "Invalid email/mobile or password.",
                "error"
            )

            return render_template(
                "login.html"
            )


        role = normalize_role(role)


        if not role:

            flash(
                "Invalid account role.",
                "error"
            )

            return render_template(
                "login.html"
            )


        # =================================================
        # SESSION
        # =================================================

        session.clear()

        session.permanent = remember

        session["user_id"] = user_id

        session["name"] = name

        session["email"] = email

        session["mobile"] = mobile

        session["role"] = role


        if (
            preferred_language
            in SUPPORTED_LANGUAGES
        ):

            session["language"] = (
                preferred_language
            )

        else:

            session["language"] = "en"


        # =================================================
        # ROLE REDIRECT
        # =================================================

        if role == "farmer":

            return redirect(
                url_for("farmer.farmer")
            )


        if role == "consumer":

            return redirect(
                url_for("consumer.consumer")
            )


        if role == "admin":

            return redirect(
                url_for("admin.admin")
            )


        return redirect(
            url_for("login")
        )


    except Exception as exc:

        print(
            "LOGIN ERROR:",
            repr(exc)
        )

        flash(
            "Login failed. Please try again.",
            "error"
        )

        return render_template(
            "login.html"
        )


    finally:

        if connection:

            connection.close()


# =========================================================
# SIGNUP
# =========================================================

@auth_bp.route(
    "/signup",
    methods=["GET", "POST"]
)
def signup():

    if request.method == "GET":

        return render_template(
            "signup.html"
        )


    # =====================================================
    # FORM DATA
    # =====================================================

    fullname = str(
        request.form.get(
            "fullname",
            ""
        )
    ).strip()


    mobile = str(
        request.form.get(
            "mobile",
            ""
        )
    ).strip()


    email = str(
        request.form.get(
            "email",
            ""
        )
    ).strip().lower()


    password = request.form.get(
        "password",
        ""
    )


    role = normalize_role(
        request.form.get(
            "role",
            ""
        )
    )


    # =====================================================
    # VALIDATION
    # =====================================================

    if len(fullname) < 2:

        flash(
            "Please enter your full name.",
            "error"
        )

        return render_template(
            "signup.html"
        )


    if not valid_mobile(mobile):

        flash(
            "Please enter a valid 10-digit mobile number.",
            "error"
        )

        return render_template(
            "signup.html"
        )


    if not valid_email(email):

        flash(
            "Please enter a valid email address.",
            "error"
        )

        return render_template(
            "signup.html"
        )


    if len(password) < 6:

        flash(
            "Password must contain at least 6 characters.",
            "error"
        )

        return render_template(
            "signup.html"
        )


    if not role:

        flash(
            "Please select Farmer or Consumer.",
            "error"
        )

        return render_template(
            "signup.html"
        )


    connection = None


    try:

        connection = get_db_connection()

        cursor = connection.cursor()


        # =================================================
        # CHECK EXISTING EMAIL
        # =================================================

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = LOWER(%s)
            LIMIT 1
            """,
            (email,)
        )


        existing_email = cursor.fetchone()


        if existing_email:

            flash(
                "An account with this email already exists.",
                "error"
            )

            return render_template(
                "signup.html"
            )


        # =================================================
        # CHECK EXISTING MOBILE
        # =================================================

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE mobile = %s
            LIMIT 1
            """,
            (mobile,)
        )


        existing_mobile = cursor.fetchone()


        if existing_mobile:

            flash(
                "An account with this mobile number already exists.",
                "error"
            )

            return render_template(
                "signup.html"
            )


        # =================================================
        # PASSWORD HASH
        # =================================================

        password_hash = generate_password_hash(
            password
        )


        # =================================================
        # GLOBAL LANGUAGE
        # =================================================

        preferred_language = get_language()


        # =================================================
        # INSERT USER
        # =================================================

        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                mobile,
                password_hash,
                role,
                preferred_language
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
            """,
            (
                fullname,
                email,
                mobile,
                password_hash,
                role,
                preferred_language
            )
        )


        new_user = cursor.fetchone()


        if isinstance(new_user, dict):

            new_user_id = new_user.get("id")

        else:

            new_user_id = new_user[0]


        # =================================================
        # CREATE PROFILE
        # =================================================

        if role == "farmer":

            try:

                cursor.execute(
                    """
                    INSERT INTO farmer_profiles
                    (
                        user_id
                    )
                    VALUES
                    (%s)
                    ON CONFLICT (user_id)
                    DO NOTHING
                    """,
                    (new_user_id,)
                )

            except Exception as profile_error:

                print(
                    "FARMER PROFILE WARNING:",
                    repr(profile_error)
                )


        elif role == "consumer":

            try:

                cursor.execute(
                    """
                    INSERT INTO consumer_profiles
                    (
                        user_id
                    )
                    VALUES
                    (%s)
                    ON CONFLICT (user_id)
                    DO NOTHING
                    """,
                    (new_user_id,)
                )

            except Exception as profile_error:

                print(
                    "CONSUMER PROFILE WARNING:",
                    repr(profile_error)
                )


        # =================================================
        # COMMIT
        # =================================================

        connection.commit()


        # =================================================
        # AUTO LOGIN
        # =================================================

        session.clear()

        session["user_id"] = new_user_id

        session["name"] = fullname

        session["email"] = email

        session["mobile"] = mobile

        session["role"] = role

        session["language"] = (
            preferred_language
        )


        flash(
            "Account created successfully!",
            "success"
        )


        # =================================================
        # REDIRECT
        # =================================================

        if role == "farmer":

            return redirect(
                url_for("farmer.farmer")
            )


        if role == "consumer":

            return redirect(
                url_for("consumer.consumer")
            )


        return redirect(
            url_for("login")
        )


    except Exception as exc:

        if connection:

            connection.rollback()


        print(
            "SIGNUP ERROR:",
            repr(exc)
        )


        error_text = str(exc)


        if "duplicate key" in error_text.lower():

            flash(
                "Email or mobile number already exists.",
                "error"
            )

        elif "not null" in error_text.lower():

            flash(
                "Database field is missing. Check the users table.",
                "error"
            )

        else:

            flash(
                "Unable to create account. Please try again.",
                "error"
            )


        return render_template(
            "signup.html"
        )


    finally:

        if connection:

            connection.close()


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route(
    "/logout"
)
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "GET":

        return render_template(
            "forgot_password.html"
        )


    email = str(
        request.form.get(
            "email",
            ""
        )
    ).strip().lower()


    if not valid_email(email):

        flash(
            "Enter a valid email address.",
            "error"
        )

        return render_template(
            "forgot_password.html"
        )


    connection = None


    try:

        connection = get_db_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = LOWER(%s)
            LIMIT 1
            """,
            (email,)
        )


        user = cursor.fetchone()


        if user:

            flash(
                "If the account exists, password recovery can be processed.",
                "success"
            )

        else:

            flash(
                "No account found with this email.",
                "error"
            )


        return render_template(
            "forgot_password.html"
        )


    except Exception as exc:

        print(
            "FORGOT PASSWORD ERROR:",
            repr(exc)
        )

        flash(
            "Unable to process request.",
            "error"
        )

        return render_template(
            "forgot_password.html"
        )


    finally:

        if connection:

            connection.close()


# =========================================================
# CHANGE PASSWORD
# =========================================================

@auth_bp.route(
    "/change-password",
    methods=["POST"]
)
def change_password():

    if not session.get("user_id"):

        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401


    current_password = request.form.get(
        "current_password",
        ""
    )


    new_password = request.form.get(
        "new_password",
        ""
    )


    if len(new_password) < 6:

        return jsonify({
            "success": False,
            "message":
                "New password must contain at least 6 characters."
        }), 400


    connection = None


    try:

        connection = get_db_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT password_hash
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (
                session["user_id"],
            )
        )


        user = cursor.fetchone()


        if not user:

            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404


        if isinstance(user, dict):

            password_hash = user.get(
                "password_hash"
            )

        else:

            password_hash = user[0]


        if not check_password_hash(
            password_hash,
            current_password
        ):

            return jsonify({
                "success": False,
                "message": "Current password is incorrect"
            }), 400


        new_hash = generate_password_hash(
            new_password
        )


        cursor.execute(
            """
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
            """,
            (
                new_hash,
                session["user_id"]
            )
        )


        connection.commit()


        return jsonify({
            "success": True,
            "message":
                "Password changed successfully"
        })


    except Exception as exc:

        if connection:

            connection.rollback()


        print(
            "CHANGE PASSWORD ERROR:",
            repr(exc)
        )


        return jsonify({
            "success": False,
            "message": "Unable to change password"
        }), 500


    finally:

        if connection:

            connection.close()


# =========================================================
# AUTH HEALTH
# =========================================================

@auth_bp.route(
    "/api/auth/health"
)
def auth_health():

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM users"
        )

        result = cursor.fetchone()


        if isinstance(result, dict):

            total_users = list(
                result.values()
            )[0]

        else:

            total_users = result[0]


        connection.close()


        return jsonify({
            "success": True,
            "service": "authentication",
            "database": "PostgreSQL",
            "total_users": total_users
        })


    except Exception as exc:

        print(
            "AUTH HEALTH ERROR:",
            repr(exc)
        )

        return jsonify({
            "success": False,
            "service": "authentication",
            "error": str(exc)
        }), 500
