			#Imports#

from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
from random import random
import mysql.connector
from datetime import datetime
import time
import bawss_lock

######################################################################################################################################################################################################################################

			#Variables#

cred = bawss_lock.load_config()
sql_ip = '10.0.80.1'
sql_user = cred[1]
sql_pass = cred[2]
sql_db = cred[3]
flask_secret_key = cred[4]
app = Flask(__name__)
app.config['SECRET_KEY'] = flask_secret_key
socketio = SocketIO(app, cors_allowed_origins='*')

######################################################################################################################################################################################################################################

		#Connect To SQL Database#

def sql_connect():
	mydb = mysql.connector.connect(
	  host=sql_ip,
	  user=sql_user,
	  password=sql_pass,
	  database=sql_db
	)
	return mydb

######################################################################################################################################################################################################################################

@socketio.on('connect')
def connect():
	mydb = sql_connect()
	mycursor = mydb.cursor()
	mycursor.execute('SELECT name, sale_price, reg_price, url, pic_url FROM item_information ORDER BY id DESC LIMIT 25;')
	for item in mycursor:
		percent = str(int((float(item[2].replace('$','').replace(',','')) - float(item[1].replace('$','').replace(',',''))) / float(item[2].replace('$','').replace(',','')) * 100)) + '%'
		info={
		'item_name': item[0],
		'item_price': item[2],
		'item_sale_price': item[1],
		'item_url': item[3],
		'item_pic': item[4],
		'item_percent_off': percent}
		emit('updateNewDeal',info, room=request.sid)

@app.route('/')
def home_page():
	return render_template('home.html')

@app.route('/live')
def live_view():
	return render_template('live_view.html')
	
@app.route('/about')
def about_page():
	return render_template('about.html')

@socketio.on('new_deal')
def send_deals(info):
	socketio.emit('updateNewDeal', {
	'item_name': info['item_name'],
	'item_price': info['item_price'],
	'item_sale_price': info['item_sale_price'],
	'item_url': info['item_url'],
	'item_pic': info['item_pic'],
	'item_percent_off': info['item_percent_off']})
	
######################################################################################################################################################################################################################################

