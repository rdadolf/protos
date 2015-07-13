from flask import Flask

app = Flask('protos')

@app.route('/')
def hello_world():
  return "Hello World\n"
