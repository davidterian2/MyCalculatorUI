from flask import Flask
app = Flask(CalculatorUI)

@app.route("/")
def hello():
    return "Hello World!\n"