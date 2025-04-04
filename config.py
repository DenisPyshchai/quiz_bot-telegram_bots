import os
import sys
from flask import Flask

# Folders
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{THIS_FOLDER}/venv/Lib/site-packages")
RESOURCE_FOLDER = os.path.join(THIS_FOLDER, "resources")

THIS_SERVER_ID = "id"
THIS_SERVER_AUTH_KEY = "password"

# Flask application
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None
app = Flask(__name__)

# Flask server port
SERVER_PORT = 443

# Database url
DATABASE = "postgresql://quiz_bot_messenger:1@localhost:5432/quiz_bot_messenger"

# Web interface url
WEB_INTERFACE = "http://www.quiz-bot.net:8085"
