from flask import Flask, render_template, jsonify, request, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps

URL = "ghostclient.dev"
ADMIN_PASSWORD = "Jules123."

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_host=2, x_proto=2)

def page(subdomain: str = "", route: str = "/", methods: list[str] | None = ["GET"]):
    def func(function):
        @app.route(route, endpoint=function.__name__, methods=methods)
        @wraps(function)
        def wrapper(*args, **kwargs):
            host = request.headers.get("Host", "") == f"{subdomain}.{URL}" or request.headers.get("Host", "") == f"{subdomain}{URL}"
            if host:
                return function(*args, **kwargs)
            return "404"
        return wrapper
    return func

@page("api", "/verify/<key>/<hwid>")
def verify(key, hwid):
    return jsonify({"valid": False, "resp": "Not Implemented", "key": key, "hwid": hwid})

@page("", "/admin", ["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("Password")

        if password == ADMIN_PASSWORD:
            return render_template("admin.html")
        else:
            return redirect("/")
    return render_template("adminLogin.html")

@page()
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
