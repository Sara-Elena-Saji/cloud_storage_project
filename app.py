from flask import Flask, render_template, request
import os
import uuid
import json

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
DATA_FILE = "files.json"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def load_files():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_files(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/", methods=["GET", "POST"])
def home():
    files_data = load_files()

    if request.method == "POST":
        file = request.files["file"]

        if file:
            token = str(uuid.uuid4())
            stored_name = token + "_" + file.filename

            file.save(os.path.join(app.config["UPLOAD_FOLDER"], stored_name))

            # Save metadata
            files_data.append({
                "original_name": file.filename,
                "stored_name": stored_name
            })

            save_files(files_data)

    return render_template("index.html", files=files_data)


if __name__ == "__main__":
    app.run(debug=True)