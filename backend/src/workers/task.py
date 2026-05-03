import csv
import io
from datetime import datetime, timezone, timedelta

from jinja2 import Environment, FileSystemLoader
from src.workers.workers import celery
from src.workers.mailer import send_email
from flask import current_app
from src.models import PlacementDrive, StudentProfile, Application, CompanyProfile

def _get_jinja_env():
    import os
    templates_dir = os.path.join(
        os.path.dirname(__file__), "..", "templates", "email"
    )
    return Environment(loader=FileSystemLoader(templates_dir), autoescape=True)


@celery.task(name="src.workers.task.send_daily_reminders")
def send_daily_reminders():

    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=3)
    upcoming_drives = PlacementDrive.query.filter(
        PlacementDrive.status == "approved",
        PlacementDrive.application_deadline >= now,
        PlacementDrive.application_deadline <= cutoff,
    ).all()

    if not upcoming_drives:
        print("[task] send_daily_reminders: No upcoming drives found.")
        return {"sent": 0}

    jinja_env = _get_jinja_env()
    template = jinja_env.get_template("daily_reminder.html")

    sent_count = 0
    all_students = StudentProfile.query.all()

    for drive in upcoming_drives:
        deadline = drive.application_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        days_left = (deadline - now).days + 1

        for student in all_students:
            eligible, _ = drive.is_student_eligible(student)
            if not eligible:
                continue

            already_applied = Application.query.filter_by(
                student_id=student.id, drive_id=drive.id
            ).first()
            if already_applied:
                continue

            if student.user and student.user.is_blacklisted:
                continue

            student_email = student.user.email if student.user else None
            if not student_email:
                continue

            html_body = template.render(
                student_name=student.full_name,
                job_title=drive.job_title,
                company_name=drive.company.company_name if drive.company else "Unknown",
                days_left=days_left,
                deadline=deadline.strftime("%B %d, %Y"),
                eligible_branches=drive.get_eligible_branches(),
                min_cgpa=drive.min_cgpa,
            )

            send_email(
                to=student_email,
                subject=f"Reminder: Apply to {drive.job_title} at {drive.company.company_name} — {days_left} day(s) left!",
                html_body=html_body,
            )
            sent_count += 1

    print(f"[task] send_daily_reminders: Sent {sent_count} reminder(s).")
    return {"sent": sent_count}


@celery.task(name="src.workers.task.send_monthly_report")
def send_monthly_report():
    now = datetime.now(timezone.utc)
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_label = now.strftime("%B %Y")

    drives_this_month = PlacementDrive.query.filter(
        PlacementDrive.created_at >= first_of_this_month,
        PlacementDrive.created_at <= now,
    ).all()

    applications_this_month = Application.query.filter(
        Application.applied_at >= first_of_this_month,
        Application.applied_at <= now,
    ).all()

    selected_this_month = [a for a in applications_this_month if a.status == "selected"]

    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    total_selected = Application.query.filter_by(status="selected").count()

    top_drives = (
        PlacementDrive.query
        .filter(PlacementDrive.status.in_(["approved", "closed"]))
        .all()
    )
    top_drives_sorted = sorted(top_drives, key=lambda d: len(d.applications), reverse=True)[:5]

    jinja_env = _get_jinja_env()
    template = jinja_env.get_template("monthly_report.html")

    html_body = template.render(
        month_label=month_label,
        generated_at=now.strftime("%B %d, %Y at %H:%M UTC"),
        # Monthly 
        drives_created_count=len(drives_this_month),
        applications_count=len(applications_this_month),
        selected_count=len(selected_this_month),
        # All-time totals
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications,
        total_selected=total_selected,
        # Top drives
        top_drives=[
            {
                "job_title": d.job_title,
                "company_name": d.company.company_name if d.company else "Unknown",
                "applicant_count": len(d.applications),
                "status": d.status,
            }
            for d in top_drives_sorted
        ],
    )

    admin_email = current_app.config.get("ADMIN_EMAIL", "admin@launchpad.com")
    send_email(
        to=admin_email,
        subject=f"LaunchPad Monthly Report — {month_label}",
        html_body=html_body,
    )

    print(f"[task] send_monthly_report: Report for {month_label} sent to {admin_email}.")
    return {"month": month_label, "drives": len(drives_this_month), "applications": len(applications_this_month)}


@celery.task(name="src.workers.task.export_applications_csv")
def export_applications_csv(student_id: int, student_email: str):
    student = StudentProfile.query.get(student_id)
    if not student:
        print(f"[task] export_applications_csv: Student {student_id} not found.")
        return {"error": "Student not found"}

    applications = Application.query.filter_by(student_id=student_id).order_by(
        Application.applied_at.desc()
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Student ID",
        "Student Name",
        "Company Name",
        "Job Title",
        "Drive Status",
        "Application Status",
        "Applied Date",
        "Last Updated",
    ])

    for app in applications:
        company_name = ""
        job_title = ""
        drive_status = ""
        if app.drive:
            job_title = app.drive.job_title
            drive_status = app.drive.status
            if app.drive.company:
                company_name = app.drive.company.company_name

        writer.writerow([
            student_id,
            student.full_name,
            company_name,
            job_title,
            drive_status,
            app.status,
            app.applied_at.strftime("%Y-%m-%d %H:%M UTC") if app.applied_at else "",
            app.updated_at.strftime("%Y-%m-%d %H:%M UTC") if app.updated_at else "",
        ])

    csv_bytes = output.getvalue().encode("utf-8")
    output.close()

    jinja_env = _get_jinja_env()
    template = jinja_env.get_template("csv_export_done.html")
    html_body = template.render(
        student_name=student.full_name,
        application_count=len(applications),
        generated_at=datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC"),
    )

    filename = f"placement_history_{student_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"

    send_email(
        to=student_email,
        subject=" Your Placement History Export — LaunchPad",
        html_body=html_body,
        attachments=[{
            "filename": filename,
            "data": csv_bytes,
            "mimetype": "text/csv",
        }],
    )

    print(f"[task] export_applications_csv: CSV with {len(applications)} rows sent to {student_email}.")
    return {"student_id": student_id, "rows": len(applications), "email": student_email}
