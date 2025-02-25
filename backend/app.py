import boto3
import pandas as pd
import os
import uuid  # For unique DynamoDB keys
from flask import Flask, jsonify
from bluesky import RunEngine
from ophyd.sim import motor, det
from bluesky.plans import scan
import time
from dotenv import load_dotenv

load_dotenv()
# Flask Setup
app = Flask(__name__)


# AWS DynamoDB Configuration (Use Environment Variables for Security)
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "BlueskyExperiments")

# Initialize DynamoDB
dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

print(f"✅ Connected to DynamoDB Table: {DYNAMODB_TABLE_NAME}")

response = table.scan()
print(response)

# Initialize RunEngine
RE = RunEngine()


# Function to Simulate Experiment Data
def generate_fake_data():
    docs = []

    def collect_data(name, doc):
        if name == "event":  # Only collect event data
            docs.append(doc)

    RE.subscribe(collect_data)
    RE(scan([det], motor, 10, 50, 10))  # Simulate experiment

    # Convert collected data into a list of dictionaries
    data_list = []
    for d in docs:
        if "data" in d:
            data_list.append(
                {
                    "id": str(uuid.uuid4()),  # Unique ID for DynamoDB
                    "seq_num": int(d["seq_num"]),  # Keep numbers as int
                    "time": str(d["time"]),  # Convert to string for storage
                    "motor": str(d["data"]["motor"]),
                    "motor_setpoint": str(d["data"]["motor_setpoint"]),
                    "det": str(d["data"]["det"]),
                }
            )

    # **Sort data by seq_num before inserting into DynamoDB**
    data_list.sort(key=lambda x: x["seq_num"])  # Sorting by sequence number

    print("\n✅ Ordered Data:\n", pd.DataFrame(data_list))  # Print sorted data

    return data_list


# API: Upload Data to DynamoDB
@app.route("/api/upload-dynamodb", methods=["GET"])
def upload_data():
    data = generate_fake_data()

    if not data:
        print("\n❌ ERROR: No data to upload to DynamoDB!\n")
        return

    try:
        with table.batch_writer() as batch:
            for item in data:
                batch.put_item(Item=item)

        print("\n✅ Data successfully uploaded to DynamoDB!\n")

    except Exception as e:
        print("\n❌ Upload Error:", str(e), "\n")


# Run Upload Function
upload_data()


# API: Retrieve Data from DynamoDB
@app.route("/api/get-dynamodb", methods=["GET"])
def get_dynamodb_data():
    try:
        response = table.scan()  # Fetch all data
        items = response.get("Items", [])

        if not isinstance(items, list):  # Ensure it returns an array
            return jsonify({"error": "Data is not an array"}), 500

        return jsonify(items), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
