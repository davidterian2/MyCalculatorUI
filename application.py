from flask import Flask, request
import requests
import pyodbc
from azure.identity import DefaultAzureCredential
import struct

app = Flask(__name__)

AZURE_FUNCTION_URL = "http://4.149.153.91/api/CalculateCouble" # Replace with your Azure Function URL

SQL_SERVER = "calculatorui-server.database.windows.net"
SQL_DATABASE = "calculatorui-database"
SQL_DRIVER = "ODBC Driver 18 for SQL Server"  # Adjust if needed

def log_to_sql(phrase, result):
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/.default")
        access_token = bytes(token.token, "utf-8")
        exptoken = struct.pack("=i", len(access_token)) + access_token

        conn_str = f"DRIVER={{{SQL_DRIVER}}};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};Authentication=ActiveDirectoryMsi"

        with pyodbc.connect(conn_str, attrs_before={1256: exptoken}) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO CalculationLog (Phrase, Result) VALUES (?, ?)",
                    phrase, result
                )
                conn.commit()
    except Exception as e:
        print("Logging failed:", e)

@app.route("/", methods=["GET", "POST"])
def calculator():
    result = ""
    if request.method == "POST":
        try:
            num1 = request.form["num1"]
            num2 = request.form["num2"]
            operation = request.form["operation"]

            # Create the phrase: e.g., "4 + 5"
            op_symbol = {
                "add": "+",
                "subtract": "-",
                "multiply": "*",
                "divide": "/"
            }.get(operation, "?")

            phrase = f"{num1} {op_symbol} {num2}"

            # Send POST request to Azure Function
            response = requests.post(AZURE_FUNCTION_URL, data={"phrase": phrase})
            if response.ok:
                result = response.text
            else:
                result = f"Error from Azure Function: {response.status_code}"

        except Exception as e:
            result = f"Error: {str(e)}"

         # Log to Azure SQL
        log_to_sql(phrase, result)

    return f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .calculator {{
                    background-color: #fff;
                    padding: 2rem;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    width: 300px;
                    text-align: center;
                }}
                input, select, button {{
                    margin: 0.5rem 0;
                    padding: 0.5rem;
                    width: 100%;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    font-size: 1rem;
                }}
                button {{
                    background-color: #007bff;
                    color: white;
                    border: none;
                    cursor: pointer;
                }}
                button:hover {{
                    background-color: #0056b3;
                }}
                .result {{
                    margin-top: 1rem;
                    font-weight: bold;
                    font-size: 1.2rem;
                }}
            </style>
        </head>
        <body>
            <div class="calculator">
                <h1>Calculator</h1>
                <form method="post">
                    <input type="text" name="num1" placeholder="First number" required>
                    <input type="text" name="num2" placeholder="Second number" required>
                    <select name="operation">
                        <option value="add">+</option>
                        <option value="subtract">−</option>
                        <option value="multiply">×</option>
                        <option value="divide">÷</option>
                    </select>
                    <button type="submit">Calculate</button>
                </form>
                <div class="result">Result: {result}</div>
            </div>
        </body>
    </html>
    """
