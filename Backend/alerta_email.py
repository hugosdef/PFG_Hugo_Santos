# alerta_email.py

import os
import smtplib
import zipfile
import tempfile
import shutil
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import    MIMEText
from email.mime.base import    MIMEBase

# ---------- Configuración SMTP ------------
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = os.environ.get("ALERT_MAIL_USER", "pruebaseguridad76@gmail.com")
SMTP_PASSWORD = os.environ.get("ALERT_MAIL_PASS", "cubu stmd lhpf lqzx")

MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25 MB

def send_suspicious_alert(recipient: str,
                          reasons: list[str],
                          captures_dir: str):
    """
    
    Envía un email con las 'reasons' y adjunta un ZIP de las capturas
    almacenadas en 'captures_dir'.
    - Si no hay capturas, lo notifica en el cuerpo del mensaje.
    - Si el ZIP excede 25MB, no lo adjunta y lo avisa.

    """

    # 1) Montar mensaje
    msg = MIMEMultipart()
    msg["From"]    = SMTP_USER
    msg["To"]      = recipient
    msg["Subject"] = "Alerta: comportamientos sospechosos detectados"


    # 2) Texto base
    lines = [
        "Se ha detectado comportamiento sospechoso por las siguientes razones:", ""
    ]
    lines += [f"- {r}" for r in reasons]
    lines.append("")

    imgs = []
    if os.path.isdir(captures_dir):
        imgs = [f for f in os.listdir(captures_dir)
                if os.path.isfile(os.path.join(captures_dir, f))]

    attach_path = None
    tmpdir = None

    if not imgs:
        lines.append("No se encontraron capturas para adjuntar.")
    else:
        # 3) Crear un temp dir para ZIP
        tmpdir = tempfile.mkdtemp()
        zip_path = os.path.join(tmpdir, "capturas_sospechosas.zip")
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for img in imgs:
                    full = os.path.join(captures_dir, img)
                    zf.write(full, arcname=img)
            size = os.path.getsize(zip_path)
            if size <= MAX_ATTACHMENT_SIZE:
                attach_path = zip_path
                lines.append(f"Se adjunta ZIP con {len(imgs)} capturas ({size//1024} KB).")
            else:
                lines.append("El ZIP de capturas supera 25MB, no se adjunta.")
        except Exception as e:
            lines.append(f"Error al crear ZIP: {e}")

    # 4) Adjuntar cuerpo de texto
    msg.attach(MIMEText("\n".join(lines), "plain"))

    # 5) Adjuntar el ZIP si se ha generado y cabe
    if attach_path:
        with open(attach_path, "rb") as f:
            part = MIMEBase("application", "zip")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition",
                        f"attachment; filename={os.path.basename(attach_path)}")
        msg.attach(part)

    # 6) Enviar
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[INFO] Alerta enviada a {recipient}.")
    except Exception as e:
        print(f"[ERROR] Al enviar email: {e}")
    finally:
        # 7) Limpiar tempdir si se creó
        if tmpdir and os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)
