from fastapi import FastAPI
from database import create_tables
from database import get_db
from pydantic import BaseModel
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
create_tables()

class BookingRequest(BaseModel):
    site_hash: str
    service_id: int
    customer_name: str
    phone: str
    appointment_date: str
    appointment_time: str


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/widget/{site_hash}")
def serve_widget(site_hash: str):
    return FileResponse("static/widget.html")

@app.get("/api/widget/{site_hash}")
def get_widget_config(site_hash: str):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM businesses WHERE site_hash = ?",
            (site_hash,)
        )

        business = cursor.fetchone()

        if business is None:
            raise HTTPException(
                status_code=404,
                detail="Business not found"
            )
        cursor.execute(
            "SELECT id, name FROM services WHERE business_id = ?",
            (business["id"],)
        )

        services = cursor.fetchall()

        return {
            "site_hash": business["site_hash"],
            "business_name": business["business_name"],
            "services": [dict(service) for service in services]
        }

    finally:
        conn.close()


@app.post("/api/bookings")
def create_booking(booking: BookingRequest):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id FROM businesses WHERE site_hash = ?",
            (booking.site_hash,)
        )

        business = cursor.fetchone()

        if business is None:
            raise HTTPException(404, "Business not found")

        business_id = business["id"]

        cursor.execute(
            """
            SELECT id FROM services
            WHERE id = ? AND business_id = ?
            """,
            (booking.service_id, business_id)
        )

        service = cursor.fetchone()

        if service is None:
            raise HTTPException(404, "Service not found")

        cursor.execute(
            """
            SELECT id FROM bookings
            WHERE business_id = ?
            AND appointment_date = ?
            AND appointment_time = ?
            AND status = 'confirmed'
            """,
            (
                business_id,
                booking.appointment_date,
                booking.appointment_time
            )
        )

        existing_booking = cursor.fetchone()

        if existing_booking:
            raise HTTPException(409, "This time slot is already booked")

        cursor.execute(
            """
            INSERT INTO bookings (
                business_id,
                service_id,
                customer_name,
                phone,
                appointment_date,
                appointment_time
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                business_id,
                booking.service_id,
                booking.customer_name,
                booking.phone,
                booking.appointment_date,
                booking.appointment_time
            )
        )

        booking_id = cursor.lastrowid
        conn.commit()

        return {
            "message": "Booking created successfully",
            "booking_id": booking_id
        }

    finally:
        conn.close()




@app.post("/seed")
def seed_database():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO businesses
        (site_hash, business_name)
        VALUES (?, ?)
    """, ("693b134a4ca12", "Example Dental Clinic"))

    cursor.execute(
        "SELECT id FROM businesses WHERE site_hash = ?",
        ("693b134a4ca12",)
    )

    business_id = cursor.fetchone()["id"]

    cursor.execute("""
        INSERT INTO services (business_id, name)
        SELECT ?, 'Dental Checkup'
        WHERE NOT EXISTS (
            SELECT 1 FROM services
            WHERE business_id = ? AND name = 'Dental Checkup'
        )
    """, (business_id, business_id))

    cursor.execute("""
        INSERT INTO services (business_id, name)
        SELECT ?, 'Teeth Cleaning'
        WHERE NOT EXISTS (
            SELECT 1 FROM services
            WHERE business_id = ? AND name = 'Teeth Cleaning'
        )
    """, (business_id, business_id))

    conn.commit()
    conn.close()

    return {"message": "Demo data created"}
