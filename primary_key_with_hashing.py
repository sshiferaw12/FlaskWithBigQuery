import hashlib

def generate_hashed_key(email, name):
    key = f"{email}|{name}"
    return hashlib.sha256(key.encode()).hexdigest()

def check_duplicate(id):
    query = f"""
        SELECT COUNT(*) as count FROM `{client.project}.{DATASET_NAME}.{TABLE_NAME}`
        WHERE id = '{id}'
    """
    query_job = client.query(query)
    result = query_job.result()
    count = list(result)[0]["count"]
    return count > 0



    if check_duplicate(email):
        return jsonify({"error": "Duplicate email found"}), 400

    id = str(uuid.uuid4())


def check_duplicate(email):
    query = f"""
        SELECT COUNT(*) as count FROM `{client.project}.{DATASET_NAME}.{TABLE_NAME}`
        WHERE email = '{email}'
    """
    query_job = client.query(query)
    result = query_job.result()
    count = list(result)[0]["count"]
    return count > 0



def check_duplicate_(email):
    query = f"""
        SELECT COUNT(*) as count FROM `{client.project}.{DATASET_NAME}.{TABLE_NAME}`
        WHERE email = '{email}'
    """
    query_job = client.query(query)
    result = query_job.result()

    count = list(result)[0]["count"]
    return count > 0
