sudo lsof -i tcp:80 -s tcp:listen
export FLASK_APP=server.py
python3 -m flask run --host=127.0.0.1 --port=8000
