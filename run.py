"""Local development entry point.

Run with: python run.py
This is also the command Docker uses to start the container (see Dockerfile).
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # debug is off on purpose: the Werkzeug debugger must not be reachable
    # when the container is exposed on a network.
    app.run(host="0.0.0.0", port=5000, debug=False)
