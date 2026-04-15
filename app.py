from flask import Flask, render_template, request, send_from_directory, redirect, url_for
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
        folder = request.form.get("folder", "default")

        if file:
            token = str(uuid.uuid4())
            stored_name = token + "_" + file.filename
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], stored_name))

            share_token = str(uuid.uuid4())

            files_data.append({
                "original_name": file.filename,
                "stored_name": stored_name,
                "share_token": share_token,
                "pinned": False,
                "folder": folder
            })

            save_files(files_data)

    # ⭐ sort pinned first
    files_data = sorted(files_data, key=lambda x: x.get("pinned", False), reverse=True)

    return render_template("index.html", files=files_data)


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/delete/<filename>")
def delete_file(filename):
    files_data = load_files()

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    files_data = [f for f in files_data if f["stored_name"] != filename]
    save_files(files_data)

    return redirect(url_for("home"))


@app.route("/share/<token>")
def share_file(token):
    files_data = load_files()

    for file in files_data:
        if file["share_token"] == token:
            return send_from_directory(
                app.config["UPLOAD_FOLDER"],
                file["stored_name"],
                as_attachment=True
            )

    return "Invalid or expired link"


@app.route("/create_folder", methods=["POST"])
def create_folder():
    folder_name = request.form.get("folder_name")

    if folder_name:
        pass  # will improve later

    return redirect(url_for("home"))


@app.route("/pin/<filename>")
def pin_file(filename):
    files_data = load_files()

    for file in files_data:
        if file["stored_name"] == filename:
            file["pinned"] = not file.get("pinned", False)

    save_files(files_data)

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)