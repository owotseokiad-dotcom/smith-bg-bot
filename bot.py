from flask import Flask
import threading

app = Flask(__name__)
@app.route('/')
def home(): return "SMITH BG BOT EN LIGNE"

def run_web():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_web).start()
