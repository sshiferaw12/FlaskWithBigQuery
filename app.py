import os
import uuid
from datetime import datetime, timezone

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

        # Get current timestamp for created_at and updated_at
        current_time = datetime.now(timezone.utc).isoformat()
        id = str(uuid.uuid4())
        table_id = f"{client.project}.{DATASET_NAME}.{PROFESSOR_TABLE}"

        rows_to_insert = [{
            "id": id,
            "name": name,
            "email": email,
            "department_id": department_id,
            "created_at": current_time,
            "updated_at": current_time
        }]

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

@app.route("/update_professor/<professor_id>", methods=["POST"])
def update_professor(professor_id):
    name = request.form.get("name")
    email = request.form.get("email")
    department_id = request.form.get("department_id")

    # Get current timestamp
    current_time = datetime.now(timezone.utc).isoformat()

    # Validate professor exists
    prof_query = f"SELECT id FROM `{client.project}.{DATASET_NAME}.{PROFESSOR_TABLE}` WHERE id = '{professor_id}'"
    prof_job = client.query(prof_query)
    professor = next(prof_job.result(), None)

    if not professor:
        return jsonify({"status": "error", "message": "Professor not found!"})

    # Validate department exists
    dept_query = f"SELECT id FROM `{client.project}.{DATASET_NAME}.{DEPARTMENT_TABLE}` WHERE id = '{department_id}'"
    dept_job = client.query(dept_query)

    if dept_job.result().total_rows == 0:
        return jsonify({"status": "error", "message": "Invalid department ID!"})

    # Insert the updated record with the new timestamps
    insert_query = f"""
        INSERT INTO `{client.project}.{DATASET_NAME}.{PROFESSOR_TABLE}` 
        (id, name, email, department_id, created_at, updated_at)
        VALUES 
        ('{professor_id}', '{name}', '{email}', '{department_id}', '{current_time}', '{current_time}')
    """
    try:
        client.query(insert_query).result()  # Insert the updated record

        # Batch delete previous versions (records with the same professor_id)
        delete_query = f"""
            DELETE FROM `{client.project}.{DATASET_NAME}.{PROFESSOR_TABLE}`
            WHERE id = '{professor_id}' AND updated_at < '{current_time}'
        """

        job_config = bigquery.QueryJobConfig(priority=bigquery.QueryPriority.BATCH)
        client.query(delete_query, job_config=job_config)

        return jsonify({"status": "success", "message": "Professor updated successfully!"})

    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"})


@app.route("/add_department", methods=["GET", "POST"])
def add_department():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        id = str(uuid.uuid4())

        if check_duplicate_(id):
            return jsonify({"status": "error", "message": "A unique id can not be repeated!"})

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

def check_duplicate_(id):
    query = f"""
        SELECT COUNT(*) as count FROM `{client.project}.{DATASET_NAME}.{DEPARTMENT_TABLE}`
        WHERE id = '{id}'
    """
    query_job = client.query(query)
    result = query_job.result()

    count = list(result)[0]["count"]
    return count > 0

@app.route("/professors", methods=["GET"])
def list_professors():
    # Query to fetch the latest professor record based on updated_at using JOIN
    query = f"""
            SELECT p.id, p.name, p.email, p.department_id, p.updated_at
            FROM `{client.project}.{DATASET_NAME}.{PROFESSOR_TABLE}` p
            JOIN (
                SELECT id, MAX(updated_at) AS updated_at
                FROM `{client.project}.{DATASET_NAME}.{PROFESSOR_TABLE}`
                GROUP BY id
            ) latest ON p.id = latest.id AND p.updated_at = latest.updated_at
        """

    # Fetch all departments for the dropdown in the edit form
    dept_query = f"SELECT id, name FROM `{client.project}.{DATASET_NAME}.{DEPARTMENT_TABLE}`"
    dept_job = client.query(dept_query)
    departments = [dict(row) for row in dept_job.result()]

    try:
        result = client.query(query).result()
        professors = [dict(row) for row in result]

        return render_template("professors.html", professors=professors, departments=departments)
    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)