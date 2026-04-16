from flask import Flask, render_template, request, redirect, url_for
import uuid
from supabase import create_client

app = Flask(__name__)

SUPABASE_URL = "https://fxhkjxwzilhhpwplacff.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4aGtqeHd6aWxoaHB3cGxhY2ZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNTM1MzUsImV4cCI6MjA5MTkyOTUzNX0.Rhmd2pFdnOoY40lZgQPeqE7WkLcf732icOrVS9Ds_1Q"


supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# 🚀 HOME
@app.route("/", methods=["GET", "POST"])
def home():
    selected_folder = request.args.get("folder", "all")

    # 📤 UPLOAD
    if request.method == "POST":
        file = request.files["file"]
        folder = request.form.get("folder", "default")

        if file:
            stored_name = str(uuid.uuid4()) + "_" + file.filename

            # 🔥 Upload to Supabase Storage
            supabase.storage.from_("files").upload(stored_name, file.read())

            # 🔥 Save metadata to DB
            supabase.table("files").insert({
                "original_name": file.filename,
                "stored_name": stored_name,
                "share_token": str(uuid.uuid4()),
                "pinned": False,
                "folder": folder
            }).execute()

    # 📥 FETCH FILES
    query = supabase.table("files").select("*").execute()
    files_data = query.data

    # 📁 FILTER
    if selected_folder != "all":
        files_data = [f for f in files_data if f["folder"] == selected_folder]

    # ⭐ SORT PINNED
    files_data = sorted(files_data, key=lambda x: x["pinned"], reverse=True)

    # 📂 FETCH FOLDERS
    folders = supabase.table("folders").select("*").execute().data
    folder_names = [f["name"] for f in folders]

    return render_template(
        "index.html",
        files=files_data,
        folders=folder_names,
        selected_folder=selected_folder
    )


# 📥 DOWNLOAD
@app.route("/download/<filename>")
def download_file(filename):
    url = supabase.storage.from_("files").get_public_url(filename)
    return redirect(url)


# 🔗 SHARE
@app.route("/share/<token>")
def share_file(token):
    result = supabase.table("files").select("*").eq("share_token", token).execute()

    if result.data:
        file = result.data[0]
        url = supabase.storage.from_("files").get_public_url(file["stored_name"])
        return redirect(url)

    return "Invalid link"


# ❌ DELETE FILE
@app.route("/delete/<filename>")
def delete_file(filename):
    supabase.storage.from_("files").remove([filename])
    supabase.table("files").delete().eq("stored_name", filename).execute()

    return redirect(url_for("home"))


# ⭐ PIN
@app.route("/pin/<filename>")
def pin_file(filename):
    result = supabase.table("files").select("*").eq("stored_name", filename).execute()

    if result.data:
        file = result.data[0]
        supabase.table("files").update({
            "pinned": not file["pinned"]
        }).eq("stored_name", filename).execute()

    return redirect(url_for("home"))


# 📁 CREATE FOLDER
@app.route("/create_folder", methods=["POST"])
def create_folder():
    folder_name = request.form.get("folder_name")

    if folder_name:
        supabase.table("folders").insert({"name": folder_name}).execute()

    return redirect(url_for("home"))


# 🗑 DELETE FOLDER
@app.route("/delete_folder/<folder_name>")
def delete_folder(folder_name):
    if folder_name == "default":
        return redirect(url_for("home"))

    # move files to default
    supabase.table("files").update({
        "folder": "default"
    }).eq("folder", folder_name).execute()

    # delete folder
    supabase.table("folders").delete().eq("name", folder_name).execute()

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
