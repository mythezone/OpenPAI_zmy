from flask import Flask,redirect,url_for,request,render_template

app=Flask(__name__)

@app.route("/success/<name>")
def success(name):
    return 'welecome %s'%name

@app.route("/login",methods=['POST','GET'])
def login():
    if request.method == 'POST':
        user=request.form['nm']
        return redirect(url_for('success',name=user))
    else:
        user=request.args.get('nm')
        return redirect(url_for('success',name=user))

@app.route('/')
def index():
    return render_template("hello.html")

@app.route('/hello/<user>')
def hello_name(user):
    return render_template('hello.html',name=user)


if __name__=="__main__":
    app.run(debug=True)
