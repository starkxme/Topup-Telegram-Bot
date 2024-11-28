import random
import string
from telebot import types
import telebot
import requests
import base64
import time
import io
from PIL import Image
from datetime import datetime
import http.client
import json
import os
from keep_alive import keep_alive

keep_alive()
# Initialize the bot with your Telegram bot token
bot = telebot.TeleBot("7503406993:AAEhELn6Sq1L9QimKv_qvi-BrZFSnX5zPa8")  # Replace with your bot token

# Define the API endpoint and headers
url = 'https://khqr.sanawin.icu/khqr/create'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjY5Nzk0LCJpYXQiOjE3MzAzODczMjksImV4cCI6MTczMjk3OTMyOX0.cjkkxXYOEgWTuaB2UEPupHY4Nta6kI7-IxMo5TxTXwg'  # Replace with your API token
}

# Price list dictionary
price_list = {
    "86": 1.15, "172": 2.22, "257": 3.12, "343": 4.25, "429": 5.30, "514": 6.45,
    "600": 7.47, "706": 8.50, "792": 10.20, "878": 11.00, "963": 12.30, "1049": 14.30,
    "1135": 15.00, "1412": 19.00, "1584": 21.99, "1755": 23.90, "2195": 29.00,
    "2538": 34.00, "2901": 37.60, "3688": 48.00, "4394": 55.50, "5532": 70.00, "6238": 78.50,
    "6944": 89.00, "7727": 99.00, "8433": 110.00, "9288": 120.00,
    "wkp": 1.39, "2wkp": 2.78, "3wkp": 4.17, "4wkp": 5.56, "5wkp": 6.95,
    "6wkp": 8.34, "7wkp": 9.73, "8wkp": 11.12, "9wkp": 12.51, "10wkp": 13.90,
    "twilight": 7.30
}

# Define the group ID for successful transaction messages
GROUP_ID = -1002384941004  # Replace with your actual group ID

# List of admin user IDs
ADMINS = [6393000180]  # Replace with your actual admin Telegram user IDs

# Decorator to check if the user is an admin
def admin_only(func):
    def wrapper(message, *args, **kwargs):
        if message.from_user.id in ADMINS:
            return func(message, *args, **kwargs)
        else:
            bot.reply_to(message, "You are not authorized to perform this action.")
    return wrapper

# Function to get the in-game name (IGN) using the API
def get_ign(user_id, zone_id):
    conn = http.client.HTTPSConnection("api-mobile-game-nickname-checker.p.rapidapi.com")

    headers = {
        'x-rapidapi-key': "9aa6d0bb85msh2768a67fb7b37b0p143ffdjsn943e04be5036",
        'x-rapidapi-host': "api-mobile-game-nickname-checker.p.rapidapi.com",
        'Content-Type': "application/json"
    }

    conn.request("GET", f"/mobile-legend?userId={user_id}&zoneId={zone_id}", headers=headers)

    res = conn.getresponse()
    data = res.read()

    try:
        json_data = json.loads(data.decode("utf-8"))
        ign = json_data.get("nickname", "Invalid Name ❌")  # Default to "Unknown" if not found
        return ign
    except json.JSONDecodeError:
        return "Error parsing response"

# Command to edit price
@bot.message_handler(commands=['edit_price'])
@admin_only
def edit_price(message):
    msg = bot.send_message(
        message.chat.id, 
        "Enter the item and new price in the format: `item new_price` (e.g., `86 0.06`)", 
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_price_update)

def process_price_update(message):
    try:
        user_input = message.text.split()
        if len(user_input) != 2:
            raise ValueError("Invalid format. Use: `item new_price`.")
        
        item, new_price = user_input
        if item not in price_list:
            raise ValueError(f"Item `{item}` not found in the price list.")
        
        price_list[item] = float(new_price)
        bot.reply_to(message, f"Price for `{item}` has been updated to ${float(new_price):.2f}.")
    except ValueError as e:
        bot.reply_to(message, str(e))
        bot.register_next_step_handler(message, process_price_update)
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

# Start and help command
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use the buttons below to view the product list or select a game category.")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("MLBB", "Free Fire")
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

# Handle MLBB price list display
@bot.message_handler(func=lambda message: message.text == 'MLBB')
def show_price_buttons(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    items = list(price_list.items())
    
    for i in range(0, len(items), 2):
        row = []
        for j in range(2):
            if i + j < len(items):
                item, price = items[i + j]
                row.append(types.KeyboardButton(f"{item} - ${price:.2f}"))
        markup.add(*row)
    
    markup.add(types.KeyboardButton("Back"))
    bot.send_message(message.chat.id, "Choose an item from the price list:", reply_markup=markup)

# Handle back command
@bot.message_handler(func=lambda message: message.text == 'Back')
def go_back_to_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("MLBB", "Free Fire")
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

# Handle item selection
@bot.message_handler(func=lambda message: any(item in message.text for item in price_list.keys()))
def handle_item_selection(message):
    try:
        item_text = message.text.split(" - ")[0]
        if item_text not in price_list:
            raise ValueError("Invalid item selection.")
        price = price_list[item_text]
        msg = bot.send_message(message.chat.id, f"You selected `{item_text}` priced at ${price:.2f}. Enter your UserID and ServerID in the format: `userid serverid`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_user_input, item_text, price)
    except ValueError as e:
        bot.reply_to(message, str(e))
        show_price_buttons(message)

# Process user input for UserID and ServerID
def process_user_input(message, item, price):
    try:
        user_input = message.text.split()
        if len(user_input) != 2:
            raise ValueError("Invalid format. Use: `userid serverid`.")
        userid, serverid = user_input
        
        # Get the user's in-game name (IGN)
        ign = get_ign(userid, serverid)
        bot.reply_to(message, f"Your in-game name (IGN) is: {ign}")
        
        generate_qr_code(message, price, userid, serverid, item, ign)
    except ValueError as e:
        bot.reply_to(message, str(e))
        bot.register_next_step_handler(message, process_user_input, item, price)

# Generate QR code for the transaction
# Generate QR code for the transaction
def generate_qr_code(message, amount, userid, serverid, item, ign):
    if ign == "Invalid Name ❌":
        bot.reply_to(message, "Invalid in-game name. Please check your UserID and ServerID and try again.")
        return  # Exit the function if the name is invalid
    
    payload = {
        "type": "personal",
        "data": {
            "bakongAccountID": "lyhang_hyper@aclb",
            "accName": "SKIBIDI SHOP",
            "accountInformation": "090854415",
            "currency": "USD",
            "amount": amount,
            "address": "PhnomPenh"
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        response_data = response.json()
        if response_data['success']:
            qr_code_base64 = response_data['data']['qrCodeImage']
            md5 = response_data['data']['md5']
            qr_code_bytes = base64.b64decode(qr_code_base64.split(',', 1)[1])

            # Build the message with user details and the amount
            message_text = (
                f"```Scan the QR Code to pay```\n"
                f"*User ID:* `{userid}`\n"
                f"*Server ID:* `{serverid}`\n"
                f"*Name:* `{ign}`\n"
                f"*Item:* `{item}`\n"
                f"*Amount:* `{amount}$`"
            )

            bot.send_photo(message.chat.id, qr_code_bytes, message_text, parse_mode="Markdown")

            # Start a background task to check transaction status periodically
            check_transaction_periodically(message, md5, userid, serverid, item)
        else:
            bot.reply_to(message, f"Failed to generate QR code: {response_data.get('message', 'No message provided.')}")
    else:
        bot.reply_to(message, f"Request failed with status code: {response.status_code}")


# Periodically check the transaction status
# Periodically check the transaction status
def check_transaction_periodically(message, md5, userid, serverid, item, retries=5):
    attempt = 0
    while attempt < retries:
        try:
            time.sleep(30)  # Wait before checking again
            url = "https://khqr.sanawin.icu/khqr/check-transaction"
            payload = {
                "md5": md5,
                "bakongToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiOTFhNzgzZmQwOWE5NGQxIn0sImlhdCI6MTczMDM4Nzc1MSwiZXhwIjoxNzM4MTYzNzUxfQ.jSBGdjXNmznbcc5wXO5J-PEevLfraJIIESMODAJvjyo"
            }

            response = requests.post(url, json=payload, headers=headers)
            if response.status_code in [200, 201]:
                response_data = response.json()
                if response_data['status'] != 'fail':
                    # Transaction success
                    amount = price_list[item]
                    ign = get_ign(userid, serverid)  # Retrieve the user's in-game name
                    success_message = (
                        "New Order Successfully ❇️\n"
                        f"User ID: `{userid}`\n"
                        f"Server ID: `{serverid}`\n"
                        f"Name / ឈ្មោះ : *{ign}*\n"
                        f"Diamond / កញ្ចប់: `{item}`\n"
                        f"Price / តម្លៃ : `${amount:.2f}`\n"
                        f"Status / ស្ថានភាព : `Successfully` ✅"
                    )
                    bot.send_message(message.chat.id, success_message, parse_mode="Markdown")
                    bot.send_message(GROUP_ID, success_message, parse_mode="Markdown")
                    return  # Exit once successful

            attempt += 1

        except Exception as e:
            bot.reply_to(message, f"An error occurred during transaction check: {e}")
            break

    # If we exhausted all retries without success
    bot.send_message(message.chat.id, "Transaction failed or expired. Please try again.")


# Run the bot
bot.infinity_polling()
