import sqlite3
import os
from pathlib import Path


# =========================================================
# CALAWLA DENTAL CLINIC
# DATABASE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "calawla.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    connection = get_db()

    cursor = connection.cursor()


    # =====================================================
    # APPOINTMENTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            phone TEXT NOT NULL,

            email TEXT,

            service TEXT NOT NULL,

            appointment_date TEXT NOT NULL,

            appointment_time TEXT NOT NULL,

            message TEXT,

            status TEXT DEFAULT 'Pending',

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # =====================================================
    # SAFE DATABASE MIGRATION
    # =====================================================

    cursor.execute("""
        PRAGMA table_info(appointments)
    """)

    columns = [

        row["name"]

        for row in cursor.fetchall()

    ]


    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    if "status" not in columns:

        cursor.execute("""
            ALTER TABLE appointments
            ADD COLUMN status
            TEXT DEFAULT 'Pending'
        """)


    # -----------------------------------------------------
    # CREATED AT
    # -----------------------------------------------------

    if "created_at" not in columns:

        cursor.execute("""
            ALTER TABLE appointments
            ADD COLUMN created_at
            TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        """)


    connection.commit()

    connection.close()


# =========================================================
# CREATE APPOINTMENT
# =========================================================

def create_appointment(
    name,
    phone,
    email,
    service,
    appointment_date,
    appointment_time,
    message
):

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO appointments (

            name,

            phone,

            email,

            service,

            appointment_date,

            appointment_time,

            message,

            status

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        name,

        phone,

        email,

        service,

        appointment_date,

        appointment_time,

        message,

        "Pending"

    ))


    appointment_id = cursor.lastrowid


    connection.commit()

    connection.close()


    return appointment_id


# =========================================================
# GET SINGLE APPOINTMENT
# =========================================================

def get_appointment(
    appointment_id
):

    connection = get_db()


    appointment = connection.execute(
        """
        SELECT *

        FROM appointments

        WHERE id = ?

        """,

        (
            appointment_id,
        )

    ).fetchone()


    connection.close()


    return appointment


# =========================================================
# GET ALL APPOINTMENTS
# =========================================================

def get_all_appointments():

    connection = get_db()


    appointments = connection.execute("""
        SELECT *

        FROM appointments

        ORDER BY id DESC
    """).fetchall()


    connection.close()


    return appointments


# =========================================================
# GET PENDING APPOINTMENTS
# =========================================================

def get_pending_appointments():

    connection = get_db()


    appointments = connection.execute("""
        SELECT *

        FROM appointments

        WHERE status = 'Pending'

        ORDER BY appointment_date ASC,
                 appointment_time ASC
    """).fetchall()


    connection.close()


    return appointments


# =========================================================
# GET CONFIRMED APPOINTMENTS
# =========================================================

def get_confirmed_appointments():

    connection = get_db()


    appointments = connection.execute("""
        SELECT *

        FROM appointments

        WHERE status = 'Confirmed'

        ORDER BY appointment_date ASC,
                 appointment_time ASC
    """).fetchall()


    connection.close()


    return appointments


# =========================================================
# GET CANCELLED APPOINTMENTS
# =========================================================

def get_cancelled_appointments():

    connection = get_db()


    appointments = connection.execute("""
        SELECT *

        FROM appointments

        WHERE status = 'Cancelled'

        ORDER BY appointment_date DESC,
                 appointment_time DESC
    """).fetchall()


    connection.close()


    return appointments


# =========================================================
# UPDATE APPOINTMENT STATUS
# =========================================================

def update_appointment_status(
    appointment_id,
    status
):

    allowed_statuses = [

        "Pending",

        "Confirmed",

        "Cancelled"

    ]


    if status not in allowed_statuses:

        return False


    connection = get_db()


    cursor = connection.execute(
        """
        UPDATE appointments

        SET status = ?

        WHERE id = ?

        """,

        (

            status,

            appointment_id

        )

    )


    connection.commit()


    updated = cursor.rowcount


    connection.close()


    return updated > 0


# =========================================================
# DELETE APPOINTMENT
# =========================================================

def delete_appointment(
    appointment_id
):

    connection = get_db()


    cursor = connection.execute(
        """
        DELETE FROM appointments

        WHERE id = ?

        """,

        (
            appointment_id,
        )

    )


    connection.commit()


    deleted = cursor.rowcount


    connection.close()


    return deleted > 0


# =========================================================
# COUNT ALL APPOINTMENTS
# =========================================================

def count_appointments():

    connection = get_db()


    total = connection.execute("""
        SELECT COUNT(*)

        FROM appointments
    """).fetchone()[0]


    connection.close()


    return total


# =========================================================
# COUNT PENDING
# =========================================================

def count_pending():

    connection = get_db()


    total = connection.execute("""
        SELECT COUNT(*)

        FROM appointments

        WHERE status = 'Pending'
    """).fetchone()[0]


    connection.close()


    return total


# =========================================================
# COUNT CONFIRMED
# =========================================================

def count_confirmed():

    connection = get_db()


    total = connection.execute("""
        SELECT COUNT(*)

        FROM appointments

        WHERE status = 'Confirmed'
    """).fetchone()[0]


    connection.close()


    return total


# =========================================================
# COUNT CANCELLED
# =========================================================

def count_cancelled():

    connection = get_db()


    total = connection.execute("""
        SELECT COUNT(*)

        FROM appointments

        WHERE status = 'Cancelled'
    """).fetchone()[0]


    connection.close()


    return total


# =========================================================
# TODAY'S APPOINTMENTS
# =========================================================

def count_today_appointments(
    today
):

    connection = get_db()


    total = connection.execute(
        """
        SELECT COUNT(*)

        FROM appointments

        WHERE appointment_date = ?

        AND status != 'Cancelled'
        """,

        (
            today,
        )

    ).fetchone()[0]


    connection.close()


    return total


# =========================================================
# TODAY'S APPOINTMENT LIST
# =========================================================

def get_today_appointments(
    today
):

    connection = get_db()


    appointments = connection.execute(
        """
        SELECT *

        FROM appointments

        WHERE appointment_date = ?

        AND status != 'Cancelled'

        ORDER BY appointment_time ASC
        """,

        (
            today,
        )

    ).fetchall()


    connection.close()


    return appointments


# =========================================================
# SEARCH APPOINTMENTS
# =========================================================

def search_appointments(
    search
):

    connection = get_db()


    search_value = f"%{search}%"


    appointments = connection.execute(
        """
        SELECT *

        FROM appointments

        WHERE
            name LIKE ?

            OR phone LIKE ?

            OR email LIKE ?

            OR service LIKE ?

            OR message LIKE ?

        ORDER BY id DESC
        """,

        (

            search_value,

            search_value,

            search_value,

            search_value,

            search_value

        )

    ).fetchall()


    connection.close()


    return appointments


# =========================================================
# CHECK APPOINTMENT
# =========================================================

def appointment_exists(
    appointment_date,
    appointment_time
):

    connection = get_db()


    appointment = connection.execute(
        """
        SELECT id

        FROM appointments

        WHERE appointment_date = ?

        AND appointment_time = ?

        AND status != 'Cancelled'

        LIMIT 1
        """,

        (

            appointment_date,

            appointment_time

        )

    ).fetchone()


    connection.close()


    return appointment is not None


# =========================================================
# GET DASHBOARD STATISTICS
# =========================================================

def get_dashboard_stats():

    connection = get_db()


    total = connection.execute("""
        SELECT COUNT(*)

        FROM appointments
    """).fetchone()[0]


    pending = connection.execute("""
        SELECT COUNT(*)

        FROM appointments

        WHERE status = 'Pending'
    """).fetchone()[0]


    confirmed = connection.execute("""
        SELECT COUNT(*)

        FROM appointments

        WHERE status = 'Confirmed'
    """).fetchone()[0]


    cancelled = connection.execute("""
        SELECT COUNT(*)

        FROM appointments

        WHERE status = 'Cancelled'
    """).fetchone()[0]


    connection.close()


    return {

        "total": total,

        "pending": pending,

        "confirmed": confirmed,

        "cancelled": cancelled

    }


# =========================================================
# START DATABASE
# =========================================================

if not os.environ.get('VERCEL'):
    init_db()
