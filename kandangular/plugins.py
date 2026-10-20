from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)
    app.config.update(DEBUG=False, MAX_CONTENT_LENGTH=65536)

    @app.get("/status")
    def status():
        return jsonify(component="KandangUlar Flask", status="ok")

    return app
