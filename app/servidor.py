from flask import Flask

app = Flask(__name__)
@app.route("/")

def hello():
 return "\n\tHello World!\n"

if __name__ == "__main__":
 app.run(ssl_context=('/tmp/svid.0.pem', '/tmp/svid.0.key'))