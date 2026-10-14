from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash
from database.db import get_db_connection
from services.notification_service import create_smart_notification

sos_bp = Blueprint("sos", __name__, url_prefix="/sos")
STATUSES = {"SENT", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED", "CANCELLED"}

def uid():
    try: return int(session.get("user_id") or session.get("id"))
    except: return None

def ensure_sos_table():
    conn=get_db_connection(); cur=conn.cursor()
    try:
        cur.execute("""CREATE TABLE IF NOT EXISTS sos_requests(
            id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, emergency_type VARCHAR(100) NOT NULL,
            message TEXT, location TEXT, status VARCHAR(30) DEFAULT 'SENT', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sos_user ON sos_requests(user_id,created_at DESC)")
        conn.commit()
    finally: cur.close(); conn.close()

def notify_admins(sos_id, title, message):
    conn=get_db_connection(); cur=conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE LOWER(COALESCE(role,''))='admin'")
        admins=cur.fetchall(); conn.close()
        for a in admins:
            aid=a.get("id") if isinstance(a,dict) else a[0]
            create_smart_notification(aid,title,message,"sos","SOS","CRITICAL",f"/sos/{sos_id}",str(sos_id),f"sos-{sos_id}-{title}")
    except Exception:
        try: conn.close()
        except: pass

@sos_bp.route("", methods=["GET"])
def page():
    if not uid(): return redirect(url_for("auth.login"))
    ensure_sos_table(); conn=get_db_connection(); cur=conn.cursor()
    cur.execute("SELECT id,emergency_type,message,location,status,created_at,updated_at FROM sos_requests WHERE user_id=%s ORDER BY created_at DESC LIMIT 50",(uid(),))
    rows=cur.fetchall(); cur.close(); conn.close()
    return render_template("sos.html", sos_requests=rows, role=session.get("role"))

@sos_bp.route("/create", methods=["POST"])
def create():
    if not uid(): return jsonify(success=False,message="Login required."),401
    data=request.get_json(silent=True) or request.form
    emergency=str(data.get("emergency_type") or data.get("type") or "General Emergency").strip()[:100]
    message=str(data.get("message") or "Emergency assistance requested.").strip()
    location=str(data.get("location") or session.get("location") or "").strip()[:500]
    ensure_sos_table(); conn=get_db_connection(); cur=conn.cursor()
    try:
        cur.execute("INSERT INTO sos_requests(user_id,emergency_type,message,location,status) VALUES(%s,%s,%s,%s,'SENT') RETURNING id",(uid(),emergency,message,location))
        row=cur.fetchone(); sid=row["id"] if isinstance(row,dict) else row[0]; conn.commit()
    finally: cur.close(); conn.close()
    create_smart_notification(uid(),"🚨 SOS Request Created",f"Your SOS request for {emergency} has been sent. Status: SENT.","sos","SOS","CRITICAL",f"/sos/{sid}",str(sid),f"sos-{sid}-created")
    notify_admins(sid,"🚨 New SOS Emergency",f"SOS #{sid}: {emergency}. {message}")
    return jsonify(success=True,sos_id=sid,status="SENT"),201


@sos_bp.route("/admin", methods=["GET"])
def admin_page():
    if str(session.get("role", "")).lower() != "admin":
        return jsonify(success=False, message="Admin access required."), 403
    ensure_sos_table(); conn=get_db_connection(); cur=conn.cursor()
    cur.execute("SELECT id,user_id,emergency_type,message,location,status,created_at,updated_at FROM sos_requests ORDER BY created_at DESC LIMIT 200")
    rows=cur.fetchall(); cur.close(); conn.close()
    return jsonify(success=True, sos_requests=[dict(r) for r in rows])

@sos_bp.route("/<int:sos_id>", methods=["GET"])
def detail(sos_id):
    if not uid(): return redirect(url_for("auth.login"))
    ensure_sos_table(); conn=get_db_connection(); cur=conn.cursor()
    cur.execute("SELECT * FROM sos_requests WHERE id=%s AND user_id=%s",(sos_id,uid())); row=cur.fetchone(); cur.close(); conn.close()
    if not row: return "SOS not found",404
    return render_template("sos_detail.html", sos=row, role=session.get("role"))

@sos_bp.route("/<int:sos_id>/status", methods=["POST"])
def status(sos_id):
    if not uid(): return jsonify(success=False,message="Login required."),401
    data=request.get_json(silent=True) or {}; new=str(data.get("status") or "").upper()
    if new not in STATUSES: return jsonify(success=False,message="Invalid status."),400
    ensure_sos_table(); conn=get_db_connection(); cur=conn.cursor()
    try:
        role=str(session.get("role","")).lower()
        if role=="admin": cur.execute("SELECT user_id FROM sos_requests WHERE id=%s",(sos_id,))
        else: cur.execute("SELECT user_id FROM sos_requests WHERE id=%s AND user_id=%s",(sos_id,uid()))
        row=cur.fetchone()
        if not row: return jsonify(success=False,message="SOS not found."),404
        owner=row.get("user_id") if isinstance(row,dict) else row[0]
        cur.execute("UPDATE sos_requests SET status=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s",(new,sos_id)); conn.commit()
    finally: cur.close(); conn.close()
    create_smart_notification(owner,"🚨 SOS Status Updated",f"Your SOS request has been updated. Status: {new}.","sos","SOS","CRITICAL",f"/sos/{sos_id}",str(sos_id),f"sos-{sos_id}-{new}")
    return jsonify(success=True,status=new)
