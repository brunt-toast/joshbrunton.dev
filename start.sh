rm -r ./build

python3 -m venv venv
source venv/bin/activate

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
[ -f /etc/wsl.conf ] && cmd.exe /C python3 server.py
[ -f /etc/wsl.conf ] || python3 server.py

deactivate

cd build 
python3 -m http.server 8080