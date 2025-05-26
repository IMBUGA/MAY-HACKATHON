import sqlite3
import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import os
from dotenv import load_dotenv

# Load environment variables for Twilio credentials
load_dotenv()
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio client
client = Client(account_sid, auth_token)

# Database setup
def init_db():
    conn = sqlite3.connect('appointments.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS appointments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  patient_name TEXT,
                  patient_phone TEXT,
                  doctor_name TEXT,
                  doctor_phone TEXT,
                  appointment_date TEXT,
                  appointment_time TEXT,
                  reminder_sent INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# Add a new appointment
def add_appointment(patient_name, patient_phone, doctor_name, doctor_phone, appointment_date, appointment_time):
    conn = sqlite3.connect('appointments.db')
    c = conn.cursor()
    c.execute('''INSERT INTO appointments 
                 (patient_name, patient_phone, doctor_name, doctor_phone, appointment_date, appointment_time)
                 VALUES (?, ?, ?, ?, ?, ?)''',
                 (patient_name, patient_phone, doctor_name, doctor_phone, appointment_date, appointment_time))
    conn.commit()
    conn.close()

# Send SMS reminder
def send_sms(to_number, message):
    try:
        client.messages.create(
            body=message,
            from_=twilio_phone,
            to=to_number
        )
        print(f"SMS sent to {to_number}")
        return True
    except TwilioRestException as e:
        print(f"Error sending SMS to {to_number}: {e}")
        return False

# Check and send reminders
def check_reminders():
    conn = sqlite3.connect('appointments.db')
    c = conn.cursor()
    current_time = datetime.datetime.now()
    reminder_time = current_time + datetime.timedelta(hours=24)

    # Format date for comparison
    reminder_date = reminder_time.date().isoformat()
    
    c.execute('''SELECT * FROM appointments 
                 WHERE appointment_date = ? AND reminder_sent = 0''', 
                 (reminder_date,))
    
    appointments = c.fetchall()
    
    for appt in appointments:
        appt_id, patient_name, patient_phone, doctor_name, doctor_phone, appt_date, appt_time, _ = appt
        
        # Patient reminder
        patient_message = f"Reminder: Your appointment with Dr. {doctor_name} is tomorrow at {appt_time}."
        send_sms(patient_phone, patient_message)
        
        # Doctor reminder
        doctor_message = f"Reminder: You have an appointment with {patient_name} tomorrow at {appt_time}."
        send_sms(doctor_phone, doctor_message)
        
        # Mark reminder as sent
        c.execute('UPDATE appointments SET reminder_sent = 1 WHERE id = ?', (appt_id,))
    
    conn.commit()
    conn.close()

# Example usage
if __name__ == "__main__":
    init_db()
    
    # Add sample appointment (YYYY-MM-DD format)
    add_appointment(
        patient_name="Dan Sande",
        patient_phone="+254797971425",
        doctor_name="Dr. Son",
        doctor_phone="+254740946260",
        appointment_date=(datetime.datetime.now() + datetime.timedelta(hours=24)).date().isoformat(),
        appointment_time="14:00"
    )
    
    # Check and send reminders
    check_reminders()
