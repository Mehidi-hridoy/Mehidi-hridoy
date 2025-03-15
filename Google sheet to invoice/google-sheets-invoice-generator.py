import os
import pdfkit
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import re
from num2words import num2words
import qrcode
import base64
from io import BytesIO

# Set up paths
CREDENTIALS_FILE = r'Sales.json'
SPREADSHEET_ID = 'your id name '
OUTPUT_FOLDER = r'\Invoices'

# Specify the exact path to wkhtmltopdf
path_to_wkhtmltopdf = r"C:\wkhtmltox\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

# Define scope and authenticate
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

# Fetch data from Google Sheets
def fetch_sheet_data():
    sheet = service.spreadsheets()
    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Combined!A1:Z").execute()
        rows = result.get('values', [])
        return rows
    except Exception as e:
        print(f"Error reading data: {e}")
        return []

# Group data by date and customer name
def group_data(data):
    grouped_data = {}
    for row in data[1:]:
        date = row[0] if len(row) > 0 else "Unknown Date"
        customer_number= row[2] if len(row) > 2 else 0
        customer_name = row[3] if len(row) > 3 else "Unknown Customer"
        customer_address = f"{row[5]} {row[6]} {row[7]} {row[8]} {row[9]}" if len(row) > 9 else "Unknown Address"
        call_status = row[4] if len(row) > 4 else "Unknown"
        product_name = row[11] if len(row) > 11 else "Unknown Product"
        unit = row[12] if len(row) > 12 else "Unknown Unit"
        kg_pc = row[13] if len(row) > 13 else 0
        total_value = float(row[14]) if len(row) > 14 and row[14].isdigit() else 0
        delivery_charge = extract_numeric_value(row[16]) if len(row) > 16 else 0
        call_agent_name = row[1] if len(row) > 1 else "Unknown Agent"  # Assuming 21st column is Call Agent Name
        remarks = row[10] if len(row) > 10 else "No Remarks"  # Assuming 22nd column is Remarks

        if call_status != "Ordered":
            continue
        
        key = (date, customer_name)
        
        if key not in grouped_data:
            grouped_data[key] = {
                "products": [],
                "delivery_charge": 0,
                "customer_address": customer_address,
                "customer_number": customer_number,
                "call_agent_name": call_agent_name,
                "remarks": remarks
            }
        
        grouped_data[key]["products"].append({
            "product_name": product_name,
            "unit": unit,
            "kg_pc": kg_pc,
            "total_value": total_value
        })
        
        grouped_data[key]["delivery_charge"] += delivery_charge
    
    return grouped_data


# Helper function to extract numeric value from the delivery charge string
def extract_numeric_value(value):
    try:
        return float(re.sub(r'[^\d.]', '', str(value)))
    except ValueError:
        return 0.0

# Helper function to convert numbers to words (in English)

def num_to_words(amount):
    # Define the words for numbers
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
            "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    thousands = ["", "Thousand", "Million", "Billion"]

    # Convert the amount into an integer
    amount = int(amount)

    if amount == 0:
        return "Zero Taka Only."
    
    def convert_hundreds(num):
        if num == 0:
            return ""
        elif num < 20:
            return ones[num]
        elif num < 100:
            return tens[num // 10] + (" " + ones[num % 10] if num % 10 != 0 else "")
        else:
            return ones[num // 100] + " Hundred" + (" " + convert_hundreds(num % 100) if num % 100 != 0 else "")
    
    def convert(num):
        if num == 0:
            return ""
        else:
            result = ""
            idx = 0
            while num > 0:
                if num % 1000 != 0:
                    result = convert_hundreds(num % 1000) + (" " + thousands[idx] if thousands[idx] else "") + " " + result
                num //= 1000
                idx += 1
            return result.strip()

    # Get the words for the amount
    words = convert(amount)

    # Ensure it ends with "Taka Only" and capitalize the first letter of each word
    words = ' '.join([word.capitalize() for word in words.split()])
    words += " Taka Only."

    return words


# Function to generate QR code as a base64 image
def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=3, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"
# Generate the HTML invoice with full details
def generate_html_invoice(date, customer_name, customer_number, call_agent, remarks, customer_address, products, delivery_charge):
    # Calculate totals
    subtotal = sum([product["total_value"] for product in products]) + delivery_charge
    total = subtotal
    in_words = num_to_words(total)

    # Prepare product details for QR code
    product_details = [
        {
            "name": product["product_name"],
            "unit": product["unit"],
            "kg/pc": product["kg_pc"],
            "value": product["total_value"],
        }
        for product in products
    ]

    # QR code data
    qr_data = {
        "ordered_date": date,
        "customer_name": customer_name,
        "customer_number": customer_number,
        "delivery_address": customer_address,
        "products": product_details,
        "total_value": total,
        "call_agent": call_agent,
        "remarks": remarks
    }

    # Generate QR code
    qr_code_image = generate_qr_code(qr_data)

    # Generate product rows for HTML table
    product_rows = ""
    for product in products:
        product_rows += f"""
            <tr>
                <td>{product['product_name']}</td>
                <td>{product['unit']}</td>
                <td>{product['kg_pc']}</td>
                <td>{product['total_value']}</td>
            </tr>
        """
      # HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Invoice - {customer_name} - {date}</title>
  <style>
    body {{ 
      font-family: Arial, sans-serif; 
      margin: 0; 
      padding: 0; 
      background-color: #e9f7e1; /* Light green background */
    }}
    .invoice-header, .invoice-footer {{ 
      text-align: center; 
      padding: 10px; 
      background-color: #4CAF50; /* Green header background */
      color: white;
    }}
    .invoice-header {{ font-size: 1.2em; }}
    .invoice-footer {{ background-color: #f1f1f1; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    table, th, td {{ border: 1px solid #ccc; }}
    th, td {{ padding: 8px; text-align: left; }}
    th {{ background-color: #f4f4f4; }}
    .invoice-details {{ display: flex; justify-content: space-between; margin: 20px; }}
    .remarks {{ background-color: #f4f4f4; font-weight: bold; padding: 10px; }}
    .qr-code {{ text-align: right; margin-top: 20px; }}
    .delivery-charge, .subtotal, .total {{ text-align: right; margin: 20px; font-size: 14px; }}
    .footer-note {{ font-size: 12px; margin-top: 20px; }}
  </style>
</head>
<body>
  <div class="invoice-header">
    <div class="logo">Your Company Name</div>
    <div class="details">
      Inspiring Better Food Choices<br>
      <strong>INVOICE</strong><br>
       Dhaka 1229<br>
      Phone: 8809611900222, +8801890030303<br>
      Email: support@yourcompnay.com
    </div>
  </div>

  <table>
    <tr>
      <td><strong>Customer Name:</strong> {customer_name}</td>
      <td><strong>Ordered Date:</strong> {date}</td>
    </tr>
    <tr>
      <td><strong>Customer Number:</strong> {customer_number}</td>
      <td><strong>Invoice Generated On:</strong> {datetime.now().strftime('%d-%m-%y')}</td>
    </tr>
    <tr>
      <td><strong>Delivery Address:</strong> {customer_address}</td>
      <td>&nbsp;</td> <!-- Empty cell for symmetry -->
    </tr>
  </table>

  <table>
    <thead>
      <tr>
        <th>Products Name</th>
        <th>Unit</th>
        <th>Kg/Pc</th>
        <th>Total Value</th>
      </tr>
    </thead>
    <tbody>
      {product_rows}
    </tbody>
  </table>

  <div class="delivery-charge">
    <p><strong>Delivery Charge:</strong> {delivery_charge}</p>
  </div>
  <div class="subtotal">
    <p><strong>Subtotal (Total Value + Delivery Charge):</strong> {subtotal}</p>
  </div>
  <div class="total">
    <p><strong>Total (In Words):</strong> {in_words}</p>
    <p><strong>Total (In Numbers):</strong> {total}</p>
  </div>

  <div class="remarks">
    <p><strong>Remarks:</strong> {remarks}</p>
    <p><strong>Call Agent Name:</strong> {call_agent}</p>
  </div>

  <div class="qr-code">
    <img src="{qr_code_image}" alt="QR Code">
  </div>

  <div class="footer-note">
    <p>Thank you for shopping with XYZ!</p>
  </div>
</body>
</html>
"""


    return html_content  # Ensure this is correctly indented to match the function block




# Save the HTML content as a PDF
def save_as_pdf(html_content, output_path):
    try:
        pdfkit.from_string(html_content, output_path, configuration=config)
        print(f"Invoice saved as PDF: {output_path}")
    except Exception as e:
        print(f"Error saving PDF: {e}")

def process_invoices():
    data = fetch_sheet_data()
    grouped_data = group_data(data)
    
    for (date, customer_name), data in grouped_data.items():
        customer_address = data["customer_address"]
        products = data["products"]
        delivery_charge = data["delivery_charge"]
        customer_number = data["customer_number"]
        call_agent = data["call_agent_name"]
        remarks = data["remarks"]

        html_content = generate_html_invoice(date, customer_name, customer_number, call_agent, remarks, customer_address, products, delivery_charge)
        
        output_path = os.path.join(OUTPUT_FOLDER, f"{date.replace('/', '-')}_{customer_name}_Invoice.pdf")
        save_as_pdf(html_content, output_path)

# Run the process
process_invoices()
