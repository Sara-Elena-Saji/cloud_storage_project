from flask import Flask, render_template, request
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        file = request.files["file"]

        if file:
            token = str(uuid.uuid4())
            stored_name = token + "_" + file.filename
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], stored_name))

    # Get list of files
    files = os.listdir(app.config["UPLOAD_FOLDER"])

    return render_template("index.html", files=files)


if __name__ == "__main__":
    app.run(debug=True)