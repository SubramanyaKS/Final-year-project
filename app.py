
import re
from urllib import response
from flask import Flask
from flask import request, jsonify,render_template,request,make_response
import json
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from flask_wtf import Form
from wtforms import  IntegerField, TextAreaField, SubmitField, PasswordField
from wtforms import validators, ValidationError
from wtforms.validators import DataRequired,InputRequired,Email
from wtforms.fields import EmailField
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import pbkdf2_sha256


import urllib.request
from flask import Flask,render_template, request,jsonify
import json
import time
from flask_mongoengine import MongoEngine
import requests,random


app = Flask(__name__)


app.secret_key='development key'
'''
DB_URI = "mongodb+srv://Puneeth:puneeth@cluster0.h225z.mongodb.net/IOT_ENERGY_MONITORING_SYSTEM?retryWrites=true&w=majority"
app.config["MONGODB_HOST"] = DB_URI
'''
app.config['MONGODB_SETTINGS'] = {
'db': 'IOT_ENERY_METER',
'host': 'localhost',
'port': 27017
}

db = MongoEngine()
db.init_app(app)

api_key='ILS1ZHA84G658442'
ch_id='1737989'




class blinks(db.Document):
    user_id=db.StringField()
    meter_id=db.StringField()
    blink_count=db.IntField()
    price=db.FloatField()
    date = db.StringField()
    time = db.StringField()


class register_user(db.Document):
    full_name = db.StringField()
    ph_no= db.IntField()
    email = db.EmailField()
    city = db.StringField()
    state = db.StringField()
    area = db.StringField()
    address = db.StringField()
    meter_id = db.StringField()
    thingspeak_id = db.StringField()
    password = db.StringField()
    c_password = db.StringField()
    


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/forgot')
def forgot():
    return render_template("forgot.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/change')
def change():
    return render_template("changePassword.html")




@app.route('/register_data',methods=['POST'])
def register_data():
    record = json.loads(request.data)
    password=record['password']
    c_password=record['c_password']

    user_meterid=register_user.objects(meter_id=record['meter_id'])
    user_email=register_user.objects(email=record['email'])
    user_ts_id=register_user.objects(thingspeak_id=record['ts_id'])
    

    if user_meterid or user_email or user_ts_id :
        return render_template("error.html",data="User already exists")
    else:
        if password==c_password:
            hash_password=pbkdf2_sha256.using(rounds=8000, salt_size=10).hash(record['password'])
            c = register_user( full_name=record['full_name'],
                ph_no=record['ph_no'],
                email=record['email'],
                city= record['city'],
                state= record['state'],
                area= record['area'],
                thingspeak_id=record['ts_id'],
                meter_id=record['meter_id'],
                address=record['address'],
                password=hash_password)       
            c.save()
            return render_template("success.html",data="User Registered Successfully")
        else:
            return render_template("error.html",data="Password Confirmation is Wrong")



@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='GET':
        return render_template("register.html")
    else:
        x={"full_name":request.form['full_name'],
            "ph_no":request.form['ph_no'],
            "email":request.form['email'],
            "city":request.form['city'],
            "state":request.form['state'],
            "area":request.form['area'],
            "ts_id":request.form['ts_id'],
            "meter_id":request.form['meter_id'],
            "address":request.form['address'],
            "password":request.form['password'],
            "c_password":request.form['c_password']
        }
        status=password_valid(request.form['password'])

        if(status==True):
            x=json.dumps(x)
            response=requests.post(url='http://127.0.0.1:5000/register_data',data=x)
        else:
            return render_template("error.html",data="Password should have atleast one Uppercase letter, Lowecase letter, Number and Special character")
    return response.text

def  password_valid(password):
    flag=False
    n=re.search('[0-9]',password)
    l=re.search('[a-z]',password) #Aach4ry40$
    u=re.search('[A-Z]',password)
    s=re.search('[!~@#$%^&*]',password)

    if n and l and u and s:
        flag=True
    return flag
    

@app.route('/login',methods=['GET','POST'])
def login():
    flag=True
    if request.method=='GET':
        return render_template("login.html")
    else:

        email = request.form['email']
        meter_id = request.form['meter_id']
        get_password = request.form['password'] 

        user=register_user.objects(email = email)
        user_meter_id = register_user.objects(meter_id = meter_id)
        user_password1=[str(u1.password) for u1 in user]
        user_password2 = [str(u2.password) for u2 in user_meter_id]

            #id=pbkdf2_sha256.identify(user_password[0])

        if user and user_meter_id:
            get_password1 = user_password1[0]
            get_password2 = user_password2[0]

            if get_password1==get_password2:
                decrypt=pbkdf2_sha256.verify(get_password,get_password1)
            else:
                return render_template("error.html",data="You have Entered wrong Password")

            if decrypt!=True:
                flag=False
            if flag==True:
                ts_id= [str(u2.thingspeak_id) for u2 in user_meter_id]
                if ts_id:
                    ts_id=ts_id[0]
                    data=blinks.objects(user_id=ts_id)
                    if data:
                        
                        resp=make_response(render_template("user_dashboard.html"))
                        resp.set_cookie('email',email)
                        resp.set_cookie('meter_id',meter_id)
                        
                        return render_template("profile.html",data="Successfully Logged In")
                        
                    else:
                        return render_template("error.html",data="User Not Found !")
                else:
                    return render_template("error.html",data="User Not Found !")
            else:
                return render_template("error.html",data="You have Entered wrong Password")
        else:
            return render_template("error.html",data="You have entered wrong Email or Energy meter ID",link="url_for('login')")
    



@app.route('/', methods=['POST'])
def update_data():
    record = json.loads(request.data)
    c =blinks(user_id=record['id'],
    blink_count=record['blinks_count'],
    meter_id=record['meter_id'],
    price=record['price'],
    date=record['f_date'],
    time=record['f_time'])

    
    
    c.save()
    return ("you have consumed "+str(int(record['blinks_count'])/3200)+" KWh and Your bill is   "+str(int(record['blinks_count'])*0.00125))

@app.route('/main')
def main():
    full_doc=urllib.request.urlopen("https://api.thingspeak.com/channels/1737989/fields/1.json?api_key=ILS1ZHA84G658442")
    last_entry=urllib.request.urlopen("https://api.thingspeak.com/channels/1737989/fields/1/last.json?api_key=ILS1ZHA84G658442")
    
    response1=full_doc.read()
    response2=last_entry.read()

    data1=json.loads(response1)
    data2=json.loads(response2)

    i=data1['channel']
    ts_id=i['id']

    m_id=register_user.objects(thingspeak_id=str(ts_id))
    m_id=[str(i.meter_id) for i in m_id ]
    m_id=m_id[0]

    #d=data['feeds']

    blinks=data2['field1']

    time=data2['created_at']
    date=time.replace("Z","")
    date=date.split("T")

    f_date=date[0]
    f_time=date[1]

    data=register_user.objects(email=request.cookies.get('email'),meter_id=request.cookies.get('meter_id'))
    
    area=[str(i.area) for i in data]
    area=area[0]

    if area=="Rural":
        one_unit_price=4
    else:
        one_unit_price=7
    

    cost=int(blinks)*(one_unit_price/3200)

    x={"id":str(ts_id),
        "meter_id":m_id,
        "blinks_count":blinks,
        "f_date":f_date,
        "f_time":f_time,
        "price":cost,
    }
    x=json.dumps(x)
    response = requests.post(url="http://127.0.0.1:5000/",data=x)
 
    return jsonify(response.text)


@app.route('/get')
def get():
    data=blinks.objects()
    return render_template('get.html',data=data)


@app.route('/user_dashboard',methods=['GET','POST'])
def user_dashboard():
    data=register_user.objects(email=request.cookies.get('email'),meter_id=request.cookies.get('meter_id'))
    
    area=[str(i.area) for i in data]
    area=area[0]

    ts_id=[str(i.thingspeak_id) for i in data]
    ts_id=ts_id[0]

    user_data=blinks.objects(user_id=ts_id)
    user_price=[float(i.price) for i in user_data]
    price=user_price[-1]
    #response.set_cookie('email',email)
    #total_price=sum(user_price)

    total_units=[float(i.blink_count) for i in user_data]
    total_blinks=total_units[-1]

    total_units=total_blinks/3200

    if area=="Rural":
        one_unit_price=4
        fixed_charge=75
    else:
        one_unit_price=7
        fixed_charge=100
    #return jsonify(total_blinks)

    total_amount_to_be_paid=fixed_charge+price
    return render_template("user_dashboard.html",one_unit_price=one_unit_price,price=price,total_units=total_units,fixed_charge=fixed_charge,total_amount_to_be_paid=total_amount_to_be_paid)
    pass

@app.route('/nodemcu',methods=['POST','GET'])
def nodemcu():
    if request.method=='GET':
        return "Get method"
    else:
        data=request.json
        if data:
            return jsonify("data received")

if __name__=="__main__":
    app.run(debug=True)
