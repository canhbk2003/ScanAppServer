from crypt import methods
from flask import Flask, request, Response, render_template, redirect, url_for, session
import numpy as np
import cv2 as cv
import base64
from flask_pymongo import PyMongo
import flask
import json
from bson.json_util import dumps, loads
import urllib
from urllib.parse import unquote
from datetime import datetime

app = Flask(__name__, static_url_path = "/assets", static_folder="assets")
url = 'mongodb://127.0.0.1:27017/amgadmin'
app.config["MONGO_URI"] = url
mongodb_client = PyMongo(app)
db = mongodb_client.db

@app.route('/detect', methods=['POST'])
def detect():
	try:
		data = request.data
		nparr = np.fromstring(base64.b64decode(data), np.uint8)
		root = cv.imdecode(nparr, cv.IMREAD_COLOR)

		img = cv.cvtColor(root, cv.COLOR_BGR2GRAY)
		blur = cv.GaussianBlur(img, (3,3), 0)
		ret3, threshold3 = cv.threshold(blur, 0,255,cv.THRESH_BINARY_INV+cv.THRESH_OTSU)
		contours, hierachy = cv.findContours(threshold3, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
		c = max(contours, key=cv.contourArea)

		mask = cv.cvtColor(root, cv.COLOR_BGR2RGBA)
		mask = np.zeros_like(mask)
		cv.drawContours(mask, [c], 0, (255,255,255,255), -1)

		root2 = cv.cvtColor(root, cv.COLOR_BGR2RGBA)
		result = cv.bitwise_and(root2, mask)

		ret = cv.cvtColor(result, cv.COLOR_RGBA2BGRA)
		_, im_arr = cv.imencode('.png', ret)
		im_bytes = im_arr.tobytes()
		im_b64 = base64.b64encode(im_bytes)
		return Response(response=im_b64, status=200, mimetype='application/text')
	except:
		return Response(response='', status=500, mimetype='application/text')

@app.route('/mobilelogin', methods=['POST'])
def mobilelogin():
	error = "ok"
	_data = request.data
	data = _data.decode("utf-8")
	if data == '':
		error = "error"
	splitStr = data.split('+')
	if len(splitStr) != 2:
		error = "error"
	username = splitStr[0]
	password = splitStr[1]
	user = db.admin.find_one({"username": username, "password": password}, max_time_ms=1000)
	if not user:
		error = "error"
	_datelog = datetime.now();
	datelog = _datelog.strftime("%m/%d/%Y, %H:%M:%S")
	update_query = {"username": user["username"]}
	db.admin.update_one(update_query, {"$set":{"datelog": datelog}});
	return Response(response=error, status=200, mimetype='application/text')

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	data = None
	if request.method == 'GET':
		return render_template('login.html')
	elif request.method == 'POST':
		# check data
		if request.form["username"] == '' or request.form["password"] == '':
			error = 'Invalid user or password, please check again!'
			return render_template('login.html', error=error)
	# connect and verify data with database
	data = db.admin.find_one({"username": request.form["username"], "password": request.form["password"]}, max_time_ms=1000)
	if not data:
		error = 'Invalid user or password, please check again!'
		return render_template('login.html', error=error)
	if data["role"] == "admin":
		_datelog = datetime.now();
		datelog = _datelog.strftime("%m/%d/%Y, %H:%M:%S")
		update_query = {"username": data["username"]}
		db.admin.update_one(update_query, {"$set":{"datelog": datelog}});

		members = db.admin.find({})
		list_cursor = list(members)
		parsing_data = dumps(list_cursor, indent = 2)
		return redirect(url_for('admin', data=parsing_data))
	else:
		error = "You are not admin!"
		return render_template('login.html', error=error)

@app.route('/admin', methods=['GET'])
def admin():
	error = None
	# get data in form request body
	error = flask.request.args.get("error")
	data = flask.request.args.get("data")
	if not data or len(data) == 0:
		return redirect(url_for('login'))
	data_decoded = unquote(data)
	decoded_data = json.loads(data_decoded)
	return render_template('admin.html', data=decoded_data, error=error)

@app.route('/updateall', methods=['POST'])
def updateall():
	error = None
	if request.form["genpassword"] == '':
		error = "Password can not be empty, please check again!"
		members = db.admin.find({})
		list_cursor = list(members)
		parsing_data = dumps(list_cursor, indent = 2)
		return redirect(url_for('admin', data=parsing_data, error=error))

	password = request.form["genpassword"]
	# update new user password
	db.admin.update_many({"role":"member"}, { "$set": {"password": password}})
	# get all user and update view
	members = db.admin.find({"role":{"$eq":"member"}})
	list_cursor = list(members)
	parsing_data = dumps(list_cursor, indent = 2)
	return redirect(url_for('admin', data=parsing_data))

app.run(host="0.0.0.0", port=80)

