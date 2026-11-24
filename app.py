import os
import secrets

from flask import (
    Flask,
    abort,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from database import (
    init_db,
    create_appointment,
    get_db,
    get_appointment,
    update_appointment_status,
    delete_appointment
)


# =========================================================
# APP
# =========================================================

app = Flask(__name__, static_folder="public/static", static_url_path="/static")

app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
SITE_PREVIEW = os.environ.get("VERCEL") == "1"


# =========================================================
# ADMIN SETTINGS
# =========================================================

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")


# =========================================================
# DATABASE
# =========================================================

if not SITE_PREVIEW:
    init_db()


# =========================================================
# HELPER - ADMIN LOGIN CHECK
# =========================================================

@app.before_request
def restrict_preview():
    if SITE_PREVIEW and request.path.startswith("/admin"):
        abort(404)
    if SITE_PREVIEW and request.endpoint == "appointment":
        if request.method == "POST":
            abort(503)
        return render_template("booking_unavailable.html")


def admin_required():

    return session.get("admin_logged_in") is True


# =========================================================
# PUBLIC WEBSITE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


@app.route("/services")
def services():

    return render_template(
        "services.html"
    )


@app.route("/doctors")
def doctors():

    return render_template(
        "doctors.html"
    )


@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# =========================================================
# APPOINTMENT
# =========================================================

@app.route(
    "/appointment",
    methods=["GET", "POST"]
)
def appointment():

    if request.method == "POST":

        # -------------------------------------------------
        # GET FORM DATA
        # -------------------------------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        service = request.form.get(
            "service",
            ""
        ).strip()

        appointment_date = request.form.get(
            "appointment_date",
            ""
        ).strip()

        appointment_time = request.form.get(
            "appointment_time",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not name:

            flash(
                "Please enter your name.",
                "error"
            )

            return redirect(
                url_for("appointment")
            )


        if not phone:

            flash(
                "Please enter your phone number.",
                "error"
            )

            return redirect(
                url_for("appointment")
            )


        if not service:

            flash(
                "Please select a dental service.",
                "error"
            )

            return redirect(
                url_for("appointment")
            )


        if not appointment_date:

            flash(
                "Please select your preferred date.",
                "error"
            )

            return redirect(
                url_for("appointment")
            )


        if not appointment_time:

            flash(
                "Please select your preferred time.",
                "error"
            )

            return redirect(
                url_for("appointment")
            )


        # -------------------------------------------------
        # SAVE APPOINTMENT
        # -------------------------------------------------

        create_appointment(

            name=name,

            phone=phone,

            email=email,

            service=service,

            appointment_date=appointment_date,

            appointment_time=appointment_time,

            message=message

        )


        # -------------------------------------------------
        # SUCCESS MESSAGE
        # -------------------------------------------------

        flash(
            "Your appointment request has been submitted successfully!",
            "success"
        )


        return redirect(
            url_for("appointment")
        )


    return render_template(
        "appointment.html"
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin",
    methods=["GET", "POST"]
)
def admin_login():

    # -----------------------------------------------------
    # ALREADY LOGGED IN
    # -----------------------------------------------------

    if admin_required():

        return redirect(
            url_for("admin_dashboard")
        )


    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        # -------------------------------------------------
        # CHECK LOGIN
        # -------------------------------------------------

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session.clear()

            session[
                "admin_logged_in"
            ] = True

            session[
                "admin_username"
            ] = username


            flash(
                "Welcome back, Admin.",
                "success"
            )


            return redirect(
                url_for(
                    "admin_dashboard"
                )
            )


        # -------------------------------------------------
        # WRONG LOGIN
        # -------------------------------------------------

        flash(
            "Incorrect username or password.",
            "error"
        )


    return render_template(
        "admin_login.html"
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route(
    "/admin/dashboard"
)
def admin_dashboard():

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )


    # -----------------------------------------------------
    # FILTERS
    # -----------------------------------------------------

    search = request.args.get(
        "search",
        ""
    ).strip()


    status_filter = request.args.get(
        "status",
        "All"
    ).strip()


    date_filter = request.args.get(
        "date",
        ""
    ).strip()


    # -----------------------------------------------------
    # DATABASE CONNECTION
    # -----------------------------------------------------

    connection = get_db()


    # -----------------------------------------------------
    # BASE QUERY
    # -----------------------------------------------------

    query = """
        SELECT *
        FROM appointments
        WHERE 1 = 1
    """


    parameters = []


    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    if search:

        query += """
            AND (
                name LIKE ?
                OR phone LIKE ?
                OR email LIKE ?
                OR service LIKE ?
                OR message LIKE ?
            )
        """


        search_value = (
            f"%{search}%"
        )


        parameters.extend([

            search_value,

            search_value,

            search_value,

            search_value,

            search_value

        ])


    # -----------------------------------------------------
    # STATUS FILTER
    # -----------------------------------------------------

    allowed_statuses = [

        "Pending",

        "Confirmed",

        "Completed",

        "Cancelled"

    ]


    if status_filter in allowed_statuses:

        query += """
            AND status = ?
        """


        parameters.append(
            status_filter
        )


    # -----------------------------------------------------
    # DATE FILTER
    # -----------------------------------------------------

    if date_filter:

        query += """
            AND appointment_date = ?
        """


        parameters.append(
            date_filter
        )


    # -----------------------------------------------------
    # ORDER
    # -----------------------------------------------------

    query += """
        ORDER BY id DESC
    """


    # -----------------------------------------------------
    # GET APPOINTMENTS
    # -----------------------------------------------------

    appointments = connection.execute(

        query,

        parameters

    ).fetchall()


    # =====================================================
    # STATISTICS
    # =====================================================

    # -----------------------------------------------------
    # TOTAL
    # -----------------------------------------------------

    total = connection.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        """
    ).fetchone()[0]


    # -----------------------------------------------------
    # PENDING
    # -----------------------------------------------------

    pending = connection.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'Pending'
        """
    ).fetchone()[0]


    # -----------------------------------------------------
    # CONFIRMED
    # -----------------------------------------------------

    confirmed = connection.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'Confirmed'
        """
    ).fetchone()[0]


    # -----------------------------------------------------
    # COMPLETED
    # -----------------------------------------------------

    completed = connection.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'Completed'
        """
    ).fetchone()[0]


    # -----------------------------------------------------
    # CANCELLED
    # -----------------------------------------------------

    cancelled = connection.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'Cancelled'
        """
    ).fetchone()[0]


    # -----------------------------------------------------
    # TODAY'S APPOINTMENTS
    # -----------------------------------------------------

    from datetime import date

    today = date.today().isoformat()


    today_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE appointment_date = ?
        """,
        (today,)
    ).fetchone()[0]


    # -----------------------------------------------------
    # CLOSE DATABASE
    # -----------------------------------------------------

    connection.close()


    # -----------------------------------------------------
    # RENDER DASHBOARD
    # -----------------------------------------------------

    return render_template(

        "admin.html",

        appointments=appointments,

        total=total,

        pending=pending,

        confirmed=confirmed,

        completed=completed,

        cancelled=cancelled,

        today_count=today_count,

        search=search,

        status_filter=status_filter,

        date_filter=date_filter

    )


# =========================================================
# APPOINTMENT DETAILS
# =========================================================

@app.route(
    "/admin/appointment/<int:appointment_id>"
)
def appointment_details(
    appointment_id
):

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )


    # -----------------------------------------------------
    # GET APPOINTMENT
    # -----------------------------------------------------

    appointment = get_appointment(
        appointment_id
    )


    # -----------------------------------------------------
    # NOT FOUND
    # -----------------------------------------------------

    if appointment is None:

        flash(
            "Appointment not found.",
            "error"
        )

        return redirect(
            url_for("admin_dashboard")
        )


    # -----------------------------------------------------
    # DETAILS PAGE
    # -----------------------------------------------------

    return render_template(

        "appointment_details.html",

        appointment=appointment

    )


# =========================================================
# CONFIRM APPOINTMENT
# =========================================================

@app.route(
    "/admin/appointment/<int:appointment_id>/confirm",
    methods=["POST"]
)
def confirm_appointment(
    appointment_id
):

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )


    # -----------------------------------------------------
    # UPDATE
    # -----------------------------------------------------

    if not update_appointment_status(appointment_id, "Confirmed"):
        abort(404)


    flash(
        "Appointment confirmed successfully.",
        "success"
    )


    return redirect(
        request.referrer
        or
        url_for("admin_dashboard")
    )


# =========================================================
# COMPLETE APPOINTMENT
# =========================================================

@app.route(
    "/admin/appointment/<int:appointment_id>/complete",
    methods=["POST"]
)
def complete_appointment(
    appointment_id
):

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )


    # -----------------------------------------------------
    # UPDATE STATUS
    # -----------------------------------------------------

    if not update_appointment_status(appointment_id, "Completed"):
        abort(404)


    flash(
        "Appointment marked as completed.",
        "success"
    )


    return redirect(
        request.referrer
        or
        url_for("admin_dashboard")
    )


# =========================================================
# CANCEL APPOINTMENT
# =========================================================

@app.route(
    "/admin/appointment/<int:appointment_id>/cancel",
    methods=["POST"]
)
def cancel_appointment(
    appointment_id
):

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )


    # -----------------------------------------------------
    # UPDATE STATUS
    # -----------------------------------------------------

    if not update_appointment_status(appointment_id, "Cancelled"):
        abort(404)


    flash(
        "Appointment cancelled.",
        "error"
    )


    return redirect(
        request.referrer
        or
        url_for("admin_dashboard")
    )


# =========================================================
# DELETE APPOINTMENT
# =========================================================

@app.route(
    "/admin/appointment/<int:appointment_id>/delete",
    methods=["POST"]
)
def delete_appointment_route(
    appointment_id
):

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )


    # -----------------------------------------------------
    # DELETE
    # -----------------------------------------------------

    if not delete_appointment(appointment_id):
        abort(404)


    flash(
        "Appointment deleted successfully.",
        "success"
    )


    return redirect(
        url_for("admin_dashboard")
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route(
    "/admin/logout"
)
def admin_logout():

    # -----------------------------------------------------
    # CLEAR SESSION
    # -----------------------------------------------------

    session.clear()


    flash(
        "You have been logged out.",
        "success"
    )


    return redirect(
        url_for("admin_login")
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":

    app.run(

        debug=False,

        host="127.0.0.1",

        port=5000

    )