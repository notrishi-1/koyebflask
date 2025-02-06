import discord
from flask import Flask,jsonify
from discord.ext import commands
import threading
import random
import threading
import time
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "Discord bot is running!", 200

@app.route("/status")
def status():
    if bot.is_closed():
        return jsonify({"status": "offline"})
    return jsonify({"status": "online"})

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

    

@bot.tree.command(name="verify", description="Verifies your BMSCE email ID and assigns you the suitable role")
async def verify(interaction: discord.Interaction, email: str):
    member = interaction.user
    role = discord.utils.get(interaction.guild.roles, name="email verified")
    if role in member.roles:
        await interaction.response.send_message("You are already verified",ephemeral=True)
    else:
        otp = add_otp(interaction.user)
        try:
            if ((email.split("@"))[1]!="bmsce.ac.in"):
                await interaction.response.send_message(f"Please enter @bmsce.ac.in email ID", ephemeral=True)
            else:
            
                message = """
**OTP Sent Successfully!**

An OTP has been sent to your email address. Please use the `/validate` command to enter the OTP.

**⚠️ Important:**
- The OTP will expire in **10 minutes**.
- The email may end up in the **spam** bin, please check there.

If you didn't request this OTP, please ignore this message."""

            if(sendmail(email,otp)):
                await interaction.response.send_message(message,ephemeral=True)
            else:
                await interaction.response.send_message(f"Email Verification is down or has been disabled",ephemeral=True)
           
        except:
            await interaction.response.send_message(f"Please enter valid email ID", ephemeral=True)
       

@bot.tree.command(name="validate", description="Validates the OTP")
async def validate(interaction: discord.Interaction, otp: str):  
   message = validate_otp(interaction.user,otp)
   if(message == "OTP has been validated and the role has been assigned."):
      member = interaction.user
      role = discord.utils.get(interaction.guild.roles, name="email verified")
      if role in member.roles:
        await interaction.response.send_message("You are already verified",ephemeral=True)
      else:
        await member.add_roles(role,reason="Email Verification - ingenuity engine")
        await interaction.response.send_message(message,ephemeral=True)

def run_flask():
    app.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start() 
    bot.run('MTMzNjY5NjE3Njg3NTAxNjI4NA.GUWLFh.f726e6lmHvPGSm2SRMLRwKinm0l2RmQlktkInE')






CLIENT_ID = '1095810404910-0vimimn3us3re8op6i1m3k68qtdma8l1.apps.googleusercontent.com'
CLIENT_SECRET = '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'
REFRESH_TOKEN = '1//04AhbuGPueF1eCgYIARAAGAQSNwF-L9IrI4vMErTfKKzCBQwXhff0H7UwRwAmBqMLJZUnKHIjT4mYE0GrjC7xTL5uwK9_myh6ByM'
TOKEN_URI = 'https://oauth2.googleapis.com/token'

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def get_access_token(refresh_token):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(TOKEN_URI, data=data)
    response_data = response.json()

    if 'access_token' in response_data:
        access_token = response_data['access_token']
        return access_token
    else:
        raise Exception("Failed to obtain access token")

def send_email(access_token,toemail,otp):
    creds = Credentials(token=access_token)
    service = build('gmail', 'v1', credentials=creds)


    message = MIMEMultipart()
    message['to'] = toemail
    message['subject'] = 'OTP for BMSCE Discord Server'
    html_content = f"""
    <html>
    <body>
        <h2>OTP Verification</h2>
        <p>Your One Time Password (OTP) is <strong>{otp}</strong></p>
        <p>Thank you verifying in our server!</p>
    </body>
    </html>
    """
    message.attach(MIMEText(html_content, 'html'))
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        send_message = service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
        print(f"Email sent successfully! Message ID: {send_message['id']}")
    except Exception as error:
        print(f"An error occurred: {error}")

def sendmail(toemail,otp):
    try:
        access_token = get_access_token(REFRESH_TOKEN)
        send_email(access_token,toemail,otp)
        return True
    except:
        return False
    



otp_store = {}

def generate_otp():
    otp = random.randint(1000, 9999)  
    return otp

def add_otp(user_id):
    otp = generate_otp()
    expiration_time = time.time() + 600 


    otp_store[user_id] = {'otp': otp, 'expiration': expiration_time}
    threading.Thread(target=delete_otp, args=(user_id, expiration_time)).start()
    return otp

def delete_otp(user_id, expiration_time):
    time.sleep(600)
    
    if time.time() >= expiration_time:
        if user_id in otp_store:
            del otp_store[user_id]
            print(f"OTP for user {user_id} has expired and was deleted.")

def validate_otp(user_id, entered_otp):
    entered_otp = int(entered_otp)
    if user_id not in otp_store:
        return "OTP has expired or does not exist."
    
    otp_data = otp_store[user_id]
    if time.time() > otp_data['expiration']:
        del otp_store[user_id]  
        return "OTP has expired."
    
    if entered_otp == otp_data['otp']:
        return "OTP has been validated and the role has been assigned."
    else:
        return "Invalid OTP."






