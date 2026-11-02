import streamlit as st
import threading
import uuid

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Cinema Group Ticket Booking",
    page_icon="🎬",
    layout="wide"
)

# ==========================================
# SHARED BOOKING DATABASE AND MUTEX
# ==========================================

@st.cache_resource
def get_booking_store():
    return {
        "lock": threading.Lock(),
        "booked_seats": {
            "A3", "A4", "B7", "C2",
            "D5", "E8", "F1"
        },
        "bookings": []
    }

store = get_booking_store()
booking_lock = store["lock"]

# ==========================================
# SESSION STATE
# ==========================================

if "selected_seats" not in st.session_state:
    st.session_state.selected_seats = []

if "last_booking" not in st.session_state:
    st.session_state.last_booking = None

if "booking_error" not in st.session_state:
    st.session_state.booking_error = ""

if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""

# ==========================================
# CINEMA CONFIGURATION
# ==========================================

rows = ["A", "B", "C", "D", "E", "F"]
seats_per_row = 10
ticket_price = 150
total_seats = len(rows) * seats_per_row

# ==========================================
# TITLE
# ==========================================

st.title("🎬 Cinema Group Ticket Booking System")

st.subheader(
    "Race Condition & Mutex Based Safe Booking"
)

st.write(
    "Welcome! Select your seats and book your tickets."
)

# ==========================================
# DASHBOARD STATISTICS
# ==========================================

with booking_lock:
    booked_count = len(store["booked_seats"])

available_count = total_seats - booked_count

c1, c2, c3 = st.columns(3)

c1.metric("🎫 Total Seats", total_seats)
c2.metric("🔴 Booked Seats", booked_count)
c3.metric("🟢 Available Seats", available_count)

st.divider()

# ==========================================
# SEAT LEGEND
# ==========================================

st.subheader("Seat Information")

c1, c2, c3 = st.columns(3)

c1.markdown("🟢 Available")
c2.markdown("🟡 Selected")
c3.markdown("🔴 Booked")

# ==========================================
# THEATRE SEAT LAYOUT
# ==========================================

st.header("🎭 Theatre Seat Layout")
st.subheader("🎬 SCREEN")

for row in rows:

    cols = st.columns(seats_per_row)

    for i in range(seats_per_row):

        seat = f"{row}{i+1}"

        with booking_lock:
            is_booked = seat in store["booked_seats"]

        is_selected = seat in st.session_state.selected_seats

        if is_booked:
            label = f"🔴 {seat}"
            disabled = True

        elif is_selected:
            label = f"🟡 {seat}"
            disabled = False

        else:
            label = f"🟢 {seat}"
            disabled = False

        if cols[i].button(
            label,
            key=f"seat_{seat}",
            disabled=disabled,
            use_container_width=True
        ):

            if seat in st.session_state.selected_seats:
                st.session_state.selected_seats.remove(seat)
            else:
                st.session_state.selected_seats.append(seat)

            st.rerun()

# ==========================================
# SELECTED SEATS
# ==========================================

st.divider()

st.header("🎟️ Your Selected Seats")

if st.session_state.selected_seats:
    st.success(
        "Selected: " +
        ", ".join(st.session_state.selected_seats)
    )
else:
    st.info("Please select your seats.")

# ==========================================
# GROUP TICKET BOOKING
# ==========================================

st.divider()

st.header("👥 Group Ticket Booking")

customer_name = st.text_input(
    "Enter Customer Name",
    key="customer_name"
)

selected_count = len(st.session_state.selected_seats)

total_amount = selected_count * ticket_price

c1, c2 = st.columns(2)

c1.metric("Selected Tickets", selected_count)
c2.metric("Total Amount", f"₹{total_amount}")

st.write(f"Price per ticket: ₹{ticket_price}")

# ==========================================
# CONFIRM BOOKING
# ==========================================

if st.button(
    "🎫 Confirm Booking",
    use_container_width=True
):

    if not customer_name.strip():

        st.session_state.booking_error = (
            "Please enter customer name."
        )

    elif not st.session_state.selected_seats:

        st.session_state.booking_error = (
            "Please select at least one available seat."
        )

    else:

        booking_seats = st.session_state.selected_seats.copy()

        with booking_lock:

            unavailable = [
                seat for seat in booking_seats
                if seat in store["booked_seats"]
            ]

            if unavailable:

                st.session_state.booking_error = (
                    "These seats are already booked: "
                    + ", ".join(unavailable)
                )

            else:

                booking_id = (
                    "CIN" + uuid.uuid4().hex[:8].upper()
                )

                booking_total = len(booking_seats) * ticket_price

                booking = {
                    "booking_id": booking_id,
                    "customer": customer_name.strip(),
                    "seats": booking_seats.copy(),
                    "tickets": len(booking_seats),
                    "price": ticket_price,
                    "amount": booking_total
                }

                # Book all seats safely
                store["booked_seats"].update(booking_seats)

                # Save booking history
                store["bookings"].append(booking)

                # Save receipt in current customer session
                st.session_state.last_booking = booking

                # Clear selected seats after success
                st.session_state.selected_seats = []

                # Clear previous error
                st.session_state.booking_error = ""

               
        st.rerun()

if st.session_state.booking_error:
    st.error(st.session_state.booking_error)

# ==========================================
# BOOKING CONFIRMATION AND RECEIPT
# ==========================================

st.divider()

st.header("🧾 Booking Confirmation & Receipt")

if st.session_state.last_booking is not None:

    receipt = st.session_state.last_booking

    st.success("🎉 BOOKING CONFIRMED SUCCESSFULLY!")

    st.markdown("---")

    st.subheader("🎬 CINEMA TICKET RECEIPT")

    st.write("**Booking ID:**", receipt["booking_id"])
    st.write("**Customer Name:**", receipt["customer"])
    st.write("**Booked Seats:**", ", ".join(receipt["seats"]))
    st.write("**Number of Tickets:**", receipt["tickets"])
    st.write("**Price Per Ticket:** ₹", receipt["price"])

    st.markdown("---")

    st.subheader(
        f"💰 Total Amount: ₹{receipt['amount']}"
    )

    st.success("Thank you for booking with us!")

    receipt_text = f"""
================================
   CINEMA GROUP TICKET BOOKING
================================

BOOKING CONFIRMATION

Booking ID: {receipt['booking_id']}

Customer Name: {receipt['customer']}

Booked Seats: {', '.join(receipt['seats'])}

Number of Tickets: {receipt['tickets']}

Price Per Ticket: Rs. {receipt['price']}

TOTAL AMOUNT: Rs. {receipt['amount']}

================================
       THANK YOU!
================================
"""

    st.download_button(
        label="📥 Download Booking Receipt",
        data=receipt_text,
        file_name=f"{receipt['booking_id']}_receipt.txt",
        mime="text/plain",
        use_container_width=True
    )

else:

    st.info(
        "Your booking confirmation and receipt "
        "will appear here after successful booking."
    )

# ==========================================
# BOOKING HISTORY
# ==========================================

st.divider()

st.header("📋 Booking History")

with booking_lock:
    history = list(store["bookings"])

if history:

    for index, booking in enumerate(history, start=1):

        with st.expander(f"Booking {index}"):

            st.write("Booking ID:", booking["booking_id"])
            st.write("Customer:", booking["customer"])
            st.write("Seats:", ", ".join(booking["seats"]))
            st.write("Tickets:", booking["tickets"])
            st.write("Amount: ₹", booking["amount"])

else:

    st.info("No new bookings yet.")

# ==========================================
# MUTEX BASED BOOKING PROTECTION
# ==========================================

st.divider()

st.header("🔐 Mutex Based Booking Protection")

st.success("Mutex Lock: ENABLED")

st.write(
    "The booking system uses Python threading.Lock() "
    "to protect shared booking data."
)

st.info(
    "Only one thread can execute the protected "
    "booking operation at a time."
)

with booking_lock:
    mutex_booked = len(store["booked_seats"])
    mutex_available = total_seats - mutex_booked

c1, c2 = st.columns(2)

c1.metric("🔴 Booked Seats", mutex_booked)
c2.metric("🟢 Available Seats", mutex_available)

# ==========================================
# RACE CONDITION VS MUTEX DEMONSTRATION
# ==========================================

st.divider()

st.header("⚡ Race Condition vs Mutex Demonstration")

st.write(
    "Compare two customers trying to book the same seat A5."
)

if st.button("🚀 Run Race Condition vs Mutex Test"):

    # TEST 1: WITHOUT MUTEX

    st.subheader("1. Without Mutex")

    unsafe_seats = set()
    unsafe_results = []

    barrier = threading.Barrier(2)

    def unsafe_booking(customer):

        if "A5" not in unsafe_seats:

            barrier.wait()

            unsafe_seats.add("A5")

            unsafe_results.append(
                f"{customer}: Booking Successful"
            )

        else:

            unsafe_results.append(
                f"{customer}: Seat Already Booked"
            )

    t1 = threading.Thread(
        target=unsafe_booking,
        args=("Customer 1",)
    )

    t2 = threading.Thread(
        target=unsafe_booking,
        args=("Customer 2",)
    )

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    for result in unsafe_results:
        st.write(result)

    st.error(
        "Race Condition: Both customers passed "
        "the availability check."
    )

    # TEST 2: WITH MUTEX

    st.subheader("2. With Mutex Lock")

    safe_seats = set()
    safe_results = []

    demo_lock = threading.Lock()

    def safe_booking(customer):

        with demo_lock:

            if "A5" not in safe_seats:

                safe_seats.add("A5")

                safe_results.append(
                    f"{customer}: Booking Successful"
                )

            else:

                safe_results.append(
                    f"{customer}: Seat Already Booked"
                )

    t3 = threading.Thread(
        target=safe_booking,
        args=("Customer 1",)
    )

    t4 = threading.Thread(
        target=safe_booking,
        args=("Customer 2",)
    )

    t3.start()
    t4.start()

    t3.join()
    t4.join()

    for result in safe_results:
        st.write(result)

    st.success(
        "Mutex Protection: Only one customer "
        "successfully booked A5."
    )

# ==========================================
# PROJECT FOOTER
# ==========================================

st.divider()

st.caption(
    "Cinema Group Ticket Booking System | "
    "Python | Streamlit | Threading | Mutex Lock"
)