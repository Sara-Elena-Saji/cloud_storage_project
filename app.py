from flask import Flask, render_template, request, redirect, url_for
import uuid
import json
from supabase import create_client

app = Flask(__name__)

DATA_FILE = "files.json"

SUPABASE_URL = "https://fxhkjxwzilhhpwplacff.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4aGtqeHd6aWxoaHB3cGxhY2ZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNTM1MzUsImV4cCI6MjA5MTkyOTUzNX0.Rhmd2pFdnOoY40lZgQPeqE7WkLcf732icOrVS9Ds_1Q"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_files():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"files": [], "folders": ["default"]}


def save_files(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/", methods=["GET", "POST"])
def home():
    data = load_files()
    files_data = data["files"]
    folders = data["folders"]

    selected_folder = request.args.get("folder", "all")

    if request.method == "POST":
        file = request.files["file"]
        folder = request.form.get("folder", "default")

        if file:
            token = str(uuid.uuid4())
            stored_name = token + "_" + file.filename

            # 🔥 UPLOAD TO SUPABASE
            supabase.storage.from_("files").upload(stored_name, file.read())

            share_token = str(uuid.uuid4())

            files_data.append({
                "original_name": file.filename,
                "stored_name": stored_name,
                "share_token": share_token,
                "pinned": False,
                "folder": folder
            })

            save_files(data)

    files_data = sorted(files_data, key=lambda x: x.get("pinned", False), reverse=True)

    if selected_folder != "all":
        files_data = [f for f in files_data if f.get("folder") == selected_folder]

    return render_template("index.html", files=files_data, folders=folders, selected_folder=selected_folder)


# 🔥 DOWNLOAD
@app.route("/download/<filename>")
def download_file(filename):
    url = supabase.storage.from_("files").get_public_url(filename)
    return redirect(url)


@app.route("/share/<token>")
def share_file(token):
    data = load_files()

    for file in data["files"]:
        if file["share_token"] == token:
            url = supabase.storage.from_("files").get_public_url(file["stored_name"])
            return redirect(url)

    return "Invalid link"


@app.route("/delete/<filename>")
def delete_file(filename):
    data = load_files()

    # 🔥 DELETE FROM SUPABASE
    supabase.storage.from_("files").remove([filename])

    data["files"] = [f for f in data["files"] if f["stored_name"] != filename]
    save_files(data)

    return redirect(url_for("home"))


@app.route("/pin/<filename>")
def pin_file(filename):
    data = load_files()

    for file in data["files"]:
        if file["stored_name"] == filename:
            file["pinned"] = not file.get("pinned", False)

    save_files(data)

    return redirect(url_for("home"))


@app.route("/create_folder", methods=["POST"])
def create_folder():
    folder_name = request.form.get("folder_name")

    data = load_files()

    if folder_name and folder_name not in data["folders"]:
        data["folders"].append(folder_name)
        save_files(data)

    return redirect(url_for("home"))


@app.route("/delete_folder/<folder_name>")
def delete_folder(folder_name):
    data = load_files()

    if folder_name == "default":
        return redirect(url_for("home"))

    for file in data["files"]:
        if file.get("folder") == folder_name:
            file["folder"] = "default"

    data["folders"] = [f for f in data["folders"] if f != folder_name]

    save_files(data)

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)