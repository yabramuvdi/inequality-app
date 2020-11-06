sudo apt update
sudo apt install python3-pip tmux htop gunicorn python3-dev nginx

python3 -m pip install -U pip setuptools wheel
python3 -m pip install -r requirements.txt
pip3 install gunicorn flask

#gunicorn -w 4 -b :8000 app:server
#python3 app.py

gunicorn -w 3 --bind :8000 wsgi:application