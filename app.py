from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets API Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
SPREADSHEET_NAME = "items"
sh = client.open(SPREADSHEET_NAME)

# Open necessary sheets
inventory_sheet = sh.worksheet("Inventory")
consumption_sheet = sh.worksheet("Consumption Log")

@app.route('/')
def home():
    return render_template('mrs.html')

@app.route('/enter-consumption')
def enter_consumption():
    return render_template('enter_consumption.html')

@app.route('/view-history')
def view_history():
    return render_template('view_history.html')

@app.route('/get-items', methods=['GET'])
def get_items():
    try:
        items_data = inventory_sheet.get_all_records()
        return jsonify(items_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/log-consumption', methods=['POST'])
def log_consumption():
    try:
        data = request.json
        item_code = data["Item Code"]
        item_name = data["Item Name"]
        quantity = int(data["Quantity"])
        unit = data["Unit"]
        consumed_area = data["Consumed Area"]
        shift = data["Shift"]
        date = data["Date"]
        area_incharge = data["Area-Incharge"]
        receiver = data["Receiver"]
        contractor = data["Contractor"]

        # Validate stock
        inventory_data = inventory_sheet.get_all_records()
        for idx, row in enumerate(inventory_data):
            if str(row["Item Code"]) == str(item_code):
                physical_stock = int(row["Physical Stock"])
                if quantity > physical_stock:
                    return jsonify({"error": "Requested quantity exceeds stock!"}), 400
                new_stock = max(0, physical_stock - quantity)
                inventory_sheet.update_cell(idx + 2, 3, new_stock)
                break

        # Append to Consumption Log
        log_entry = [date, item_name, item_code, quantity, unit, consumed_area, shift, area_incharge, receiver, contractor]
        consumption_sheet.append_row(log_entry)

        return jsonify({"message": "Consumption logged successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/consumption-history', methods=['GET'])
def consumption_history():
    try:
        area_filter = request.args.get("area", "").strip()
        date_filter = request.args.get("date", "").strip()
        records = consumption_sheet.get_all_records()
        filtered_records = [
            record for record in records
            if (not area_filter or record.get("Consumed Area", "").strip() == area_filter)
            and (not date_filter or record.get("Date", "").strip() == date_filter)
        ]
        return jsonify(filtered_records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
