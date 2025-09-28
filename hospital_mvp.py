#!/usr/bin/env python3
"""
Hospital Management MVP (single-file)
Features:
- Patient management (add / view)
- Appointment scheduling (create / list)
- Basic medical records (consultation notes + prescriptions)
- Simplified billing (generate invoice)
- Admin dashboard (counts overview)

Run: python hospital_mvp.py
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "hospital_mvp.db")

# --- Database helpers ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            dob TEXT,
            phone TEXT,
            notes TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor TEXT,
            datetime TEXT,
            reason TEXT,
            status TEXT DEFAULT 'scheduled',
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER,
            patient_id INTEGER,
            doctor TEXT,
            notes TEXT,
            prescription TEXT,
            created_at TEXT,
            FOREIGN KEY(appointment_id) REFERENCES appointments(id),
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            appointment_id INTEGER,
            amount REAL,
            issued_at TEXT,
            paid INTEGER DEFAULT 0,
            FOREIGN KEY(patient_id) REFERENCES patients(id),
            FOREIGN KEY(appointment_id) REFERENCES appointments(id)
        )
    """)
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_FILE)

# --- Core operations ---
def add_patient(first, last, dob, phone, notes=""):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO patients (first_name,last_name,dob,phone,notes) VALUES (?,?,?,?,?)",
              (first,last,dob,phone,notes))
    conn.commit(); pid = c.lastrowid; conn.close()
    return pid

def list_patients():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id, first_name, last_name, dob, phone FROM patients ORDER BY id DESC")
    rows = c.fetchall(); conn.close(); return rows

def get_patient(pid):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id, first_name, last_name, dob, phone, notes FROM patients WHERE id=?", (pid,))
    r = c.fetchone(); conn.close(); return r

def add_appointment(patient_id, doctor, dt_str, reason):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO appointments (patient_id,doctor,datetime,reason) VALUES (?,?,?,?)",
              (patient_id,doctor,dt_str,reason))
    conn.commit(); aid = c.lastrowid; conn.close(); return aid

def list_appointments():
    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT a.id, p.first_name || ' ' || p.last_name AS patient, a.doctor, a.datetime, a.reason, a.status
                 FROM appointments a JOIN patients p ON a.patient_id=p.id ORDER BY a.datetime DESC""")
    rows = c.fetchall(); conn.close(); return rows

def add_consultation(appointment_id, patient_id, doctor, notes, prescription):
    conn = get_conn(); c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute("""INSERT INTO consultations (appointment_id,patient_id,doctor,notes,prescription,created_at)
                 VALUES (?,?,?,?,?,?)""", (appointment_id,patient_id,doctor,notes,prescription,created_at))
    c.execute("UPDATE appointments SET status='completed' WHERE id=?", (appointment_id,))
    conn.commit(); cid = c.lastrowid; conn.close(); return cid

def list_consultations():
    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT c.id, p.first_name || ' ' || p.last_name AS patient, c.doctor, c.created_at, c.prescription
                 FROM consultations c JOIN patients p ON c.patient_id=p.id ORDER BY c.created_at DESC""")
    rows = c.fetchall(); conn.close(); return rows

def generate_invoice(patient_id, appointment_id, amount):
    conn = get_conn(); c = conn.cursor()
    issued_at = datetime.now().isoformat()
    c.execute("INSERT INTO invoices (patient_id,appointment_id,amount,issued_at) VALUES (?,?,?,?)",
              (patient_id,appointment_id,amount,issued_at))
    conn.commit(); iid = c.lastrowid; conn.close(); return iid

def list_invoices():
    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT i.id, p.first_name || ' ' || p.last_name AS patient, i.amount, i.issued_at, i.paid
                 FROM invoices i JOIN patients p ON i.patient_id=p.id ORDER BY i.issued_at DESC""")
    rows = c.fetchall(); conn.close(); return rows

# --- Sample seed ---
def seed_sample_data():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM patients"); ifc = c.fetchone()[0]
    if ifc > 0:
        conn.close(); return
    c.execute("INSERT INTO patients (first_name,last_name,dob,phone,notes) VALUES (?,?,?,?,?)",
              ("Alice","Wong","1985-04-12","+441234567890","Allergic to penicillin"))
    c.execute("INSERT INTO patients (first_name,last_name,dob,phone,notes) VALUES (?,?,?,?,?)",
              ("Bob","Smith","1990-11-03","+447700900123","Diabetic"))
    conn.commit()
    c.execute("INSERT INTO appointments (patient_id,doctor,datetime,reason) VALUES (?,?,?,?)",
              (1,"Dr. Patel", datetime.now().isoformat(), "Routine checkup"))
    c.execute("INSERT INTO appointments (patient_id,doctor,datetime,reason) VALUES (?,?,?,?)",
              (2,"Dr. Jones", datetime.now().isoformat(), "Follow-up"))
    conn.commit(); conn.close()

# --- GUI ---
class HospitalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hospital MVP - Python/Tkinter")
        self.geometry("900x600")
        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self); notebook.pack(fill="both", expand=True)
        # Tabs
        self.pat_frame = ttk.Frame(notebook); notebook.add(self.pat_frame, text="Patients")
        self.appt_frame = ttk.Frame(notebook); notebook.add(self.appt_frame, text="Appointments")
        self.cons_frame = ttk.Frame(notebook); notebook.add(self.cons_frame, text="Consultations")
        self.bill_frame = ttk.Frame(notebook); notebook.add(self.bill_frame, text="Billing")
        self.admin_frame = ttk.Frame(notebook); notebook.add(self.admin_frame, text="Admin Dashboard")
        # Build tabs
        self.create_patients_tab(self.pat_frame)
        self.create_appointments_tab(self.appt_frame)
        self.create_consultations_tab(self.cons_frame)
        self.create_billing_tab(self.bill_frame)
        self.create_admin_tab(self.admin_frame)

    # Patients tab
    def create_patients_tab(self, parent):
        left = ttk.Frame(parent); left.pack(side="left", fill="y", padx=8, pady=8)
        right = ttk.Frame(parent); right.pack(side="right", fill="both", expand=True, padx=8, pady=8)
        self.fn = tk.StringVar(); self.ln = tk.StringVar(); self.dob = tk.StringVar(); self.phone = tk.StringVar()
        ttk.Entry(left, textvariable=self.fn).pack(fill="x", pady=2)
        ttk.Entry(left, textvariable=self.ln).pack(fill="x", pady=2)
        ttk.Entry(left, textvariable=self.dob).pack(fill="x", pady=2)
        ttk.Entry(left, textvariable=self.phone).pack(fill="x", pady=2)
        ttk.Button(left, text="Add Patient", command=self.handle_add_patient).pack(pady=6)
        ttk.Button(left, text="Refresh", command=self.refresh_patient_list).pack(pady=2)
        cols = ("id","name","dob","phone")
        self.pat_tree = ttk.Treeview(right, columns=cols, show="headings")
        for c in cols: self.pat_tree.heading(c, text=c.title())
        self.pat_tree.pack(fill="both", expand=True)
        self.pat_tree.bind("<Double-1>", self.show_patient_details)
        self.refresh_patient_list()

    def handle_add_patient(self):
        first, last, dob, phone = self.fn.get().strip(), self.ln.get().strip(), self.dob.get().strip(), self.phone.get().strip()
        if not (first and last):
            messagebox.showerror("Validation", "First and last name required"); return
        pid = add_patient(first,last,dob,phone)
        messagebox.showinfo("Added", f"Patient {first} {last} added (id {pid})")
        self.fn.set(""); self.ln.set(""); self.dob.set(""); self.phone.set("")
        self.refresh_patient_list(); self.refresh_admin()

    def refresh_patient_list(self):
        for r in self.pat_tree.get_children(): self.pat_tree.delete(r)
        for pid,f,l,dob,phone in list_patients():
            self.pat_tree.insert("", "end", values=(pid, f" {f} {l}", dob, phone))

    def show_patient_details(self, event):
        sel = self.pat_tree.selection()
        if not sel: return
        pid = self.pat_tree.item(sel[0])["values"][0]
        data = get_patient(pid)
        if not data: return
        id_, f, l, dob, phone, notes = data
        messagebox.showinfo("Patient Details", f"ID: {id_}\nName: {f} {l}\nDOB: {dob}\nPhone: {phone}\nNotes: {notes}")

    # Appointments tab
    def create_appointments_tab(self, parent):
        top = ttk.Frame(parent); top.pack(fill="x", padx=8, pady=8)
        ttk.Button(top, text="New Appointment", command=self.new_appointment_dialog).pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh_appt_list).pack(side="left", padx=6)
        cols = ("id","patient","doctor","datetime","reason","status")
        self.appt_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for c in cols: self.appt_tree.heading(c, text=c.title())
        self.appt_tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.appt_tree.bind("<Double-1>", self.open_appointment_actions)
        self.refresh_appt_list()

    def new_appointment_dialog(self):
        patients = list_patients()
        if not patients:
            messagebox.showwarning("No patients", "Please add patients first"); return
        pid = patients[0][0]
        doctor = simpledialog.askstring("Doctor", "Doctor name", initialvalue="Dr. Smith")
        dt = simpledialog.askstring("Date/time", "Enter datetime", initialvalue=datetime.now().isoformat())
        reason = simpledialog.askstring("Reason", "Reason for appointment")
        add_appointment(pid, doctor, dt, reason or "Consultation")
        self.refresh_appt_list(); self.refresh_admin()

    def refresh_appt_list(self):
        for r in self.appt_tree.get_children(): self.appt_tree.delete(r)
        for row in list_appointments(): self.appt_tree.insert("", "end", values=row)

    def open_appointment_actions(self, event):
        sel = self.appt_tree.selection()
        if not sel: return
        aid, patient, doctor, dt, reason, status = self.appt_tree.item(sel[0])["values"]
        if messagebox.askyesno("Appointment", f"Mark appointment {aid} as consultation?"):
            notes = simpledialog.askstring("Notes", "Consultation notes")
            presc = simpledialog.askstring("Prescription", "Prescription")
            conn = get_conn(); c = conn.cursor()
            c.execute("SELECT patient_id FROM appointments WHERE id=?", (aid,)); pid = c.fetchone()[0]; conn.close()
            add_consultation(aid, pid, doctor, notes or "", presc or "")
            self.refresh_appt_list(); self.refresh_consult_list(); self.refresh_admin()

    # Consultations tab
    def create_consultations_tab(self, parent):
        top = ttk.Frame(parent); top.pack(fill="x", padx=8, pady=8)
        ttk.Button(top, text="Refresh", command=self.refresh_consult_list).pack(side="left")
        cols = ("id","patient","doctor","created_at","prescription")
        self.cons_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for c in cols: self.cons_tree.heading(c, text=c.title())
        self.cons_tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.refresh_consult_list()

    def refresh_consult_list(self):
        for r in self.cons_tree.get_children(): self.cons_tree.delete(r)
        for row in list_consultations(): self.cons_tree.insert("", "end", values=row)

    # Billing tab
    def create_billing_tab(self, parent):
        top = ttk.Frame(parent); top.pack(fill="x", padx=8, pady=8)
        ttk.Button(top, text="Create Invoice", command=self.create_invoice_dialog).pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh_invoice_list).pack(side="left", padx=6)
        cols = ("id","patient","amount","issued_at","paid")
        self.inv_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for c in cols: self.inv_tree.heading(c, text=c.title())
        self.inv_tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.inv_tree.bind("<Double-1>", self.toggle_invoice_paid)
        self.refresh_invoice_list()

    def create_invoice_dialog(self):
        appts = list_appointments()
        if not appts:
            messagebox.showwarning("No appointments", "No appointments to invoice"); return
        aid = appts[0][0]
        pid = get_conn().execute("SELECT patient_id FROM appointments WHERE id=?", (aid,)).fetchone()[0]
        amount = simpledialog.askfloat("Amount", "Invoice amount", initialvalue=50.0)
        generate_invoice(pid, aid, amount)
        self.refresh_invoice_list(); self.refresh_admin()

    def refresh_invoice_list(self):
        for r in self.inv_tree.get_children(): self.inv_tree.delete(r)
        for id_, patient, amount, issued_at, paid in list_invoices():
            self.inv_tree.insert("", "end", values=(id_, patient, f"£{amount:.2f}", issued_at, "Yes" if paid else "No"))

    def toggle_invoice_paid(self, event):
        sel = self.inv_tree.selection()
        if not sel: return
        iid = self.inv_tree.item(sel[0])["values"][0]
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT paid FROM invoices WHERE id=?", (iid,)); paid = c.fetchone()[0]
        c.execute("UPDATE invoices SET paid=? WHERE id=?", (0 if paid else 1, iid)); conn.commit(); conn.close()
        self.refresh_invoice_list(); self.refresh_admin()

    # Admin dashboard
    def create_admin_tab(self, parent):
        self.stats_text = tk.Text(parent, height=10, state="disabled")
        self.stats_text.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Button(parent, text="Refresh", command=self.refresh_admin).pack()
        self.refresh_admin()

    def refresh_admin(self):
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM patients"); patients = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM appointments"); appts = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM consultations"); cons = c.fetchone()[0]
        c.execute("SELECT COUNT(*), IFNULL(SUM(amount),0) FROM invoices"); inv_count, inv_sum = c.fetchone()
        conn.close()
        txt = f"Patients: {patients}\nAppointments: {appts}\nConsultations: {cons}\nInvoices: {inv_count}\nRevenue: £{inv_sum:.2f}\n"
        self.stats_text.configure(state="normal"); self.stats_text.delete("1.0","end"); self.stats_text.insert("1.0", txt); self.stats_text.configure(state="disabled")

if __name__ == '__main__':
    init_db(); seed_sample_data()
    app = HospitalApp(); app.mainloop()
