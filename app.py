import os
import uuid

from flask import Flask, jsonify, render_template, redirect, url_for, request
from google.cloud import bigquery

app = Flask(__name__)
project_id = os.getenv("PROJECT_ID")
client = bigquery.Client(project=project_id)

DATASET_NAME = os.getenv("DATASET_NAME")
DEPARTMENT_TABLE = 'department'
PROFESSOR_TABLE = "professors"


@app.route("/departments")
def list_departments():
    query = f"SELECT * FROM `{client.project}.{DATASET_NAME}.{DEPARTMENT_TABLE}`"

    query_job = client.query(query)
    results = query_job.result()
    departments = [dict(result) for result in results]

    return render_template("departments.html", departments=departments)

@app.route("/add_department", methods=["GET", "POST"])
def add_department():
    from flask import request
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        id = str(uuid.uuid4())

        if not name or not email:
            return jsonify({"status": "error", "message": "All fields are required!"})

        table_id = f"{client.project}.{DATASET_NAME}.{DEPARTMENT_TABLE}"

        rows_to_insert = [
            {u"id":id, "name": name, u"email": email}
        ]

        errors = client.insert_rows_json(table_id, rows_to_insert)

        if errors == []:
            return redirect(url_for("list_departments"))
        else:
            return jsonify({"status": "error", "errors": errors})

    return render_template("add_department.html")

@app.route("/professors")
def list_professors():
    query = f"""
        SELECT p.id, p.name, p.email, d.name AS department_name
        FROM `{client.project}.{DATASET_NAME}.{PROFESSOR_TABLE}` AS p
        JOIN `{client.project}.{DATASET_NAME}.{DEPARTMENT_TABLE}` AS d
        ON p.department_id = d.id
    """
    query_job = client.query(query)
    professors = [dict(row) for row in query_job.result()]

    return render_template("professors.html", professors=professors)


@app.route("/add_professor", methods=["GET", "POST"])
def add_professor():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        department_id = request.form.get("department_id")

        # Validate department exists
        check_query = f"SELECT id FROM `{client.project}.{DATASET_NAME}.{DEPARTMENT_TABLE}` WHERE id = '{department_id}'"
        query_job = client.query(check_query)

        if query_job.result().total_rows == 0:
            return jsonify({"status": "error", "message": "Invalid department ID!"})

        id = str(uuid.uuid4())
        table_id = f"{client.project}.{DATASET_NAME}.{PROFESSOR_TABLE}"
        rows_to_insert = [{u"id": id, "name": name, u"email": email, u"department_id": department_id}]

        errors = client.insert_rows_json(table_id, rows_to_insert)

        if errors == []:
            return redirect(url_for("list_professors"))
        else:
            return jsonify({"status": "error", "errors": errors})

    # Fetch departments for dropdown
    dept_query = f"SELECT id, name FROM `{client.project}.{DATASET_NAME}.{DEPARTMENT_TABLE}`"
    dept_job = client.query(dept_query)
    departments = [dict(row) for row in dept_job.result()]

    return render_template("add_professor.html", departments=departments)

def check_duplicate_(email):
    query = f"""
        SELECT COUNT(*) as count FROM `{client.project}.{DATASET_NAME}.{DEPARTMENT_TABLE}`
        WHERE email = '{email}'
    """
    query_job = client.query(query)
    result = query_job.result()

    count = list(result)[0]["count"]
    return count > 0


if __name__ == '__main__':
    app.run(debug=True)