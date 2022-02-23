from flask import Flask, request, Response
import numpy as np
import cv2 as cv
import base64

app = Flask(__name__)

@app.route('/detect', methods=['POST'])
def detect():
	try:
		data = request.data
		print(data)
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
		_, im_arr = cv.imencode('.jpg', ret)
		im_bytes = im_arr.tobytes()
		im_b64 = base64.b64encode(im_bytes)
		print(im_b64)
		return Response(response=im_b64, status=200, mimetype='application/text')
	except:
		return Response(response='', status=500, mimetype='application/text')

app.run(host="0.0.0.0", port=80)




