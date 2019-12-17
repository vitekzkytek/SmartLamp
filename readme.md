# Smart Lamp Golemio
sometimes running at: http://lampa.vitekzkytek.cz/
### Run server:
`python3 -m venv lamp_env`

`source lamp_env/bin/activate`

`pip install -r requirements.txt`

`export FLASK_APP=lamp_flask`

`export FLASK_ENV=development`

`flask run --host=0.0.0.0 --port=80`

### Arduino:
Add sketch in `arduino` folder into arduino and set up wifi credentials and IP adress of the API server
