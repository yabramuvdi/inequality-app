sudo apt update
sudo apt install python3-pip tmux htop

python3 -m pip install -U pip setuptools wheel
python3 -m pip install -r requirements.txt
pip3 install gunicorn

python3 data_generation.py
gunicorn app:server -b :8000
#python3 app.py
