# app.py — the main Flask application


from flask import Flask, render_template, request
import psycopg2
import psycopg2.extras 

app = Flask(__name__)


def get_db_connection():
    conn = psycopg2.connect(
        dbname="airlines",       
        user="dooooominic",    
        password="",            
        host="localhost",
        port="5433"
    )
    return conn

#Home page
@app.route("/")
def index():
    return render_template("index.html")


#Flight searching page
@app.route("/flights")
def flights():
    # Pull the values the user typed into the form
    origin      = request.args.get("origin", "").strip().upper()
    destination = request.args.get("destination", "").strip().upper()
    start_date  = request.args.get("start_date", "")
    end_date    = request.args.get("end_date", "")


    if not origin or not destination or not start_date or not end_date:
        return render_template("index.html", error="Please fill in all fields.")


    conn = get_db_connection()

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = """
        SELECT
            f.flight_number,
            f.departure_date,
            fs.origin_code,
            fs.dest_code,
            fs.departure_time,
            fs.airline_name,
            fs.duration
        FROM Flight f
        JOIN FlightService fs ON f.flight_number = fs.flight_number
        WHERE fs.origin_code = %s AND fs.dest_code = %s AND f.departure_date BETWEEN %s AND %s
        ORDER BY f.departure_date, fs.departure_time
    """

    cursor.execute(query, (origin, destination, start_date, end_date))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

   

    for r in results:
        r["departure_time"] = r["departure_time"].strftime("%H:%M")

    # The keyword arguments become variables inside the HTML template.
    return render_template(
        "flights.html",
        flights=results,
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date
    )



@app.route("/flight/<flight_number>/<departure_date>")
def flight_detail(flight_number, departure_date):
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    info_query = """
        SELECT
            f.flight_number,
            f.departure_date,
            fs.origin_code,
            fs.dest_code,
            fs.departure_time,
            fs.airline_name,
            fs.duration,
            f.plane_type,
            a.capacity
        FROM Flight f
        JOIN FlightService fs ON f.flight_number = fs.flight_number
        JOIN Aircraft a 
        ON f.plane_type = a.plane_type
        WHERE f.flight_number  = %s AND f.departure_date = %s
    """
    cursor.execute(info_query, (flight_number, departure_date))
    flight_info = cursor.fetchone()

    if flight_info is None:
        cursor.close()
        conn.close()
        return render_template("flight.html", error="Flight not found.")

    # Count how many seats are already booked for this flight on this date.

    booking_query = """
        SELECT COUNT(*) AS booked_seats
        FROM Booking
        WHERE flight_number  = %s AND departure_date = %s
    """
    cursor.execute(booking_query, (flight_number, departure_date))
    booking_info = cursor.fetchone()

    cursor.close()
    conn.close()

    flight_info = dict(flight_info)
    flight_info["departure_time"] = flight_info["departure_time"].strftime("%H:%M")

    capacity     = flight_info["capacity"]
    booked_seats = booking_info["booked_seats"]
    available    = capacity - booked_seats #Calculate available seats

    return render_template(
        "flight.html",
        flight=flight_info,
        capacity=capacity,
        booked_seats=booked_seats,
        available=available
    )

if __name__ == "__main__":
    app.run(debug=True)
