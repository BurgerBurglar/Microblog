from app import app, db
from flask import render_template

@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html", title="404 Not Found"), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template("errors/500.html", title="500 Internal Error"), 500