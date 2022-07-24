import random
import datetime
import re
import atexit
import sched
from urllib import response
from flask import Flask
from flask import request, jsonify,render_template,request,make_response
import json
from apscheduler.schedulers.blocking import BlockingScheduler

from flask_wtf import Form
from wtforms import TextField, IntegerField, TextAreaField, SubmitField, PasswordField
from wtforms import validators, ValidationError
from wtforms.validators import DataRequired,InputRequired,Email
from wtforms.fields.html5 import EmailField
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import pbkdf2_sha256
from flask_apscheduler import APScheduler
from flask_wtf.csrf import CSRFProtect


import urllib.request
from flask import Flask,render_template, request,jsonify
import json
import time
from flask_mongoengine import MongoEngine
import requests,random
from flask_mail import *
#from flaskext.csrf import csrf

app = Flask(__name__)
#sc=APScheduler()
#csrf(app)

import config

app.secret_key='development key'
#csrf_token=CSRFProtect(app)
app.config['SECRET_KEY']='secret'
#csrf_token.init_app(app)

DB_URI = config.DB_ur
app.config["MONGODB_HOST"] = DB_URI
'''
app.config['MONGODB_SETTINGS'] = {
'db': 'IOT_ENERY_METER',
'host': 'localhost',
'port': 27017
}
'''



app.config["MAIL_SERVER"]='smtp.gmail.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = 'websiteksp.738@gmail.com'
app.config['MAIL_PASSWORD'] = 'bujostmqdvlrfyxy'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

email_app = Mail(app)

db = MongoEngine()
db.init_app(app)



api_key=config.api_key
ch_id=config.ch_id




class blinks(db.Document):
    user_id=db.StringField()
    meter_id=db.StringField()
    blink_count=db.IntField()
    price=db.FloatField()
    date = db.DateTimeField()
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



class notification(db.Document):
    notification=db.StringField()
    date=db.StringField()
    time=db.StringField()

class api_keys(db.Document):
    ch_id=db.StringField()
    api_key=db.StringField()  

class price_of_one_unit(db.Document):
    rural_price=db.FloatField()
    urban_price=db.FloatField()
    fixed_price_rural=db.FloatField()
    fixed_price_urban=db.FloatField()
    date=db.StringField()
    time=db.StringField()


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/admin')
def admin():
    return render_template("admin.html")

@app.route('/logout')
def logout():
    res=make_response(render_template("logout.html",data="Successfully Logged out"))
    res.set_cookie('email',max_age=0)
    return res

@app.route('/update_pass', methods=['PUT'])
def update_pass():
    record = json.loads(request.data)
    c = register_user.objects(email=record['email']).first()
    
    hash_pass=pbkdf2_sha256.using(rounds=8000, salt_size=10).hash(record['pass1'])
    
    if not c:
        return render_template("error.html",data="User not found for Entered email !")
    else:
        c.update(password=hash_pass)
        
    return render_template("success.html",data="Password changed successfully . ")







@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/change')
def change():
    return render_template("changePassword.html")


cookie_list=[]

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
            response=requests.post(url='https://smart-energy-monitoring.herokuapp.com/register_data',data=x)
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
    

email_cookie=[]
meter_id_cookie=[]
full_name=[]

@app.route('/login',methods=['GET','POST'])
def login():
    flag=True
    if request.method=='GET':
        return render_template("login.html")
    else:       
        email = request.form['email']
        meter_id = request.form['meter_id']
        get_password = request.form['password'] 

        if email=="admin@gmail.com" and get_password=="123":
            return render_template("admin.html")
        else:
            user=register_user.objects(email = email)
            user_meter_id = register_user.objects(meter_id = meter_id)
            user_password1=[str(u1.password) for u1 in user]
            user_password2 = [str(u2.password) for u2 in user_meter_id]

                #id=pbkdf2_sha256.identify(user_password[0])
            name=[i.full_name for i in user]
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
                    #------------------
                    '''
                    ts_id= [str(u2.thingspeak_id) for u2 in user_meter_id]
                    if ts_id:
                        ts_id=ts_id[0]
                        data=blinks.objects(user_id=ts_id)
                    #--------------------
                        if data:
                    '''
                    email_cookie.append(email)
                    meter_id_cookie.append(meter_id)
                    full_name.append(name[0])

                    #time=datetime.datetime.now()+datetime.timedelta(days=30)
                    resp=make_response(render_template("profile.html",data="Successfully Logged In"))
                    resp.set_cookie('email',email,max_age=60*60*24*365*2)
                    resp.set_cookie('meter_id',meter_id,max_age=60*60*24*365*2)
                    resp.set_cookie('name',name[0])

                    return resp
                    '''            
                    else:
                        return render_template("error.html",data="User Not Found !")
                    '''
                else:
                    return render_template("error.html",data="User Not Found !")
            else:
                return render_template("error.html",data="You have Entered wrong Password")
        '''
        else:
            return render_template("error.html",data="You have entered wrong Email or Energy meter ID",link="url_for('login')")
        '''



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
    kwh=str(int(record['blinks_count'])/3200)
    bill=str(int(record['blinks_count'])*0.00125)

    return render_template("current_status.html",kwh=kwh,bill=bill)
    #return ("you have consumed "+str(int(record['blinks_count'])/3200)+" KWh and Your bill is   "+str(int(record['blinks_count'])*0.00125))

#s=BlockingScheduler()
#@app.route('/main')
#@s.scheduled_job('interval',minutes=1)
def main_activity():
    keys={}
    data=register_user.objects()
    api_data=api_keys.objects()
    for i in api_data:
        keys[i.ch_id]=i.api_key

    for i in data:
        c_id=i.thingspeak_id
        full_doc_url="https://api.thingspeak.com/channels/"+c_id+"/fields/1.json?api_key="+keys[c_id]
        last_entry_url="https://api.thingspeak.com/channels/"+c_id+"/fields/1/last.json?api_key="+keys[c_id]

        full_doc=urllib.request.urlopen(full_doc_url)
        last_entry=urllib.request.urlopen(last_entry_url)
    
        response1=full_doc.read()
        response2=last_entry.read()

        data1=json.loads(response1)
        data2=json.loads(response2)

        

        if data2!=-1:
            i=data1['channel']
            ts_id=i['id']

            m_id=register_user.objects(thingspeak_id=str(ts_id))
            m_id=[str(i.meter_id) for i in m_id ]
            m_id=m_id[0]

            #d=data['feeds']

            blinks_from_ts=data2['field1']

            time=data2['created_at']
            date=time.replace("Z","")
            date=date.split("T")

            f_date=date[0]
            f_time=date[1]

            #data=register_user.objects(email=email_cookie[0],meter_id=meter_id_cookie[0])
            data=register_user.objects(meter_id=m_id)
        
        
            area=[str(i.area) for i in data]
            area=area[0]

            #return jsonify(area)

            if area=="Rural":
                one_unit_price=4
            else:
                one_unit_price=7
        

            cost=int( blinks_from_ts)*(one_unit_price/3200)



            """x={"id":str(ts_id),
                "meter_id":m_id,
                "blinks_count": blinks_from_ts,
                "f_date":f_date,
                "f_time":f_time,
                "price":cost,
            }
            x=json.dumps(x)
            response = requests.post(url="https://smart-energy-monitoring.herokuapp.com/",data=x)
    
            return response.text"""
            c = blinks(user_id=str(ts_id),
            blink_count= blinks_from_ts,
            meter_id=m_id,
            price=cost,
            date=f_date,
            time=f_time)        
            c.save()

#s.start()       




@app.route('/filter_wrt_date',methods=['GET','POST'])
def filter_wrt_date():
    date1=request.form['date1']
    date2=request.form['date2']
    meter_id=request.form['meter_id']

    price_data=price_of_one_unit.objects()
    #data=register_user.objects(meter_id=meter_id_cookie[0])
    data=register_user.objects(meter_id=request.cookies.get('meter_id'))
    ts_id=[str(i.thingspeak_id) for i in data]
    ts_id=ts_id[0]
    

    area=[str(i.area) for i in data]
    area=area[0]
    
    r=[i.rural_price for i in price_data]
    u=[i.urban_price for i in price_data]
    fix_r=[i.fixed_price_rural for i in price_data]
    fix_u=[i.fixed_price_urban for i in price_data]

    if area=="Rural":
        one_unit_price=r[0]
        fixed_charge=fix_r[0]
    else:
        one_unit_price=u[0]
        fixed_charge=fix_u[0]

    '''if area=="Rural":
        one_unit_price=4
        fixed_charge=75
    else:
        one_unit_price=7
        fixed_charge=100
'''
    user_data=blinks.objects(user_id=ts_id,date__gte=date1,date__lte=date2)

    if user_data:

        user_price=[float(i.price) for i in user_data]
        price=user_price[-1]
        #response.set_cookie('email',email)
        #total_price=sum(user_price)

        total_units=[float(i.blink_count) for i in user_data]
        total_blinks=total_units[-1]

        total_units=total_blinks/3200

        #return jsonify(total_blinks)

        notify=notification.objects()
        total_amount_to_be_paid=fixed_charge+price
        #return render_template("user_dashboard.html",data=notify,name=full_name[0],one_unit_price=one_unit_price,price=price,total_units=total_units,fixed_charge=fixed_charge,total_amount_to_be_paid=total_amount_to_be_paid,meter_id=meter_id)
        return render_template("user_dashboard.html",data=notify,name=request.cookies.get('name'),one_unit_price=one_unit_price,price=price,total_units=total_units,fixed_charge=fixed_charge,total_amount_to_be_paid=total_amount_to_be_paid,meter_id=meter_id)
    else:
        #return render_template("user_dashboard.html",name=full_name[0],one_unit_price=one_unit_price,price=0,total_units=0,fixed_charge=fixed_charge,total_amount_to_be_paid=fixed_charge,meter_id=meter_id)
        return render_template("user_dashboard.html",name=request.cookies.get('name'),one_unit_price=one_unit_price,price=0,total_units=0,fixed_charge=fixed_charge,total_amount_to_be_paid=fixed_charge,meter_id=meter_id)

@app.route('/get')
def get():
    data=blinks.objects()
    return render_template('get.html',data=data)


@app.route('/user_dashboard',methods=['GET','POST'])
def user_dashboard():
    data=register_user.objects(email=request.cookies.get('email'),meter_id=request.cookies.get('meter_id'))

    
    #data=register_user.objects(email=email_cookie[0],meter_id=meter_id_cookie[0])
    price_data=price_of_one_unit.objects()
    if data:
        area=[str(i.area) for i in data]
        area=area[0]

        ts_id=[str(i.thingspeak_id) for i in data]
        ts_id=ts_id[0]

        r=[i.rural_price for i in price_data]
        u=[i.urban_price for i in price_data]
        fix_r=[i.fixed_price_rural for i in price_data]
        fix_u=[i.fixed_price_urban for i in price_data]

        if area=="Rural":
            one_unit_price=r[0]
            fixed_charge=fix_r[0]
        else:
            one_unit_price=u[0]
            fixed_charge=fix_u[0]

        notify=notification.objects()
        user_data=blinks.objects(user_id=ts_id)
        if user_data():
            user_price=[float(i.price) for i in user_data]
            price=user_price[-1]
            price=float(format(price,".4f"))
            #response.set_cookie('email',email)
            #total_price=sum(user_price)

            total_units=[float(i.blink_count) for i in user_data]
            total_blinks=total_units[-1]

            total_units=total_blinks/3200

        
            #return jsonify(total_blinks)
            
            total_amount_to_be_paid=fixed_charge+price
            #return render_template("user_dashboard.html",data=notify,name=full_name[0],meter_id=meter_id_cookie[0],one_unit_price=one_unit_price,price=price,total_units=total_units,fixed_charge=fixed_charge,total_amount_to_be_paid=total_amount_to_be_paid)
            return render_template("user_dashboard.html",data=notify,name=request.cookies.get('name'),meter_id=request.cookies.get('meter_id'),one_unit_price=one_unit_price,price=price,total_units=total_units,fixed_charge=fixed_charge,total_amount_to_be_paid=total_amount_to_be_paid)
        else:
            #return render_template("user_dashboard.html",data=notify,name=full_name[0],meter_id=meter_id_cookie[0],one_unit_price=one_unit_price,price=0.0,total_units=0.0,fixed_charge=fixed_charge,total_amount_to_be_paid=fixed_charge) 
            return render_template("user_dashboard.html",data=notify,name=str(request.cookies.get('name')),meter_id=request.cookies.get('meter_id'),one_unit_price=one_unit_price,price=0.0,total_units=0.0,fixed_charge=fixed_charge,total_amount_to_be_paid=fixed_charge) 

    else:
        return render_template("error.html",data="Data Not Found")
#----------- Forgot password ---------  

otp_given=random.randint(000000,999999)
@app.route('/forgot',methods=['GET','POST'])
def forgot():

    if request.method=='GET':
        return render_template("forgot.html")
    else:
        mail=request.form['email']
        data=register_user.objects(email=mail)
        if data:
            with email_app.connect() as con:
                msgs = Message(recipients=[mail],body = "Your OTP is - "+str(otp_given), subject = 'Forgot password', sender = 'websiteksp.738@gmail.com')
                con.send(msgs)
            return render_template("forgot_submit_otp.html",data=mail)

        else:
            return render_template("error.html",data="User does not exists..!!")
            pass
        '''pass1=request.form['pass1']
        pass2=request.form['pass2']
        if pass1==pass2:
            x={"email":mail,
            "pass1":pass1,
            "pass2":pass2
            }
            x=json.dumps(x)
            response = requests.put(url="https://smart-energy-monitoring.herokuapp.com/update_pass",data=x)
            return response.text'''
        
        #return jsonify(data)

@app.route('/forgot_submit_otp',methods=['GET','POST'])
def forgot_submit_otp():
    if request.method=='GET':
        return render_template("forgot_submit_otp.html")
    else:
        mail=request.form['email']
        otp=request.form['otp']
        if int(otp)==int(otp_given):
            return render_template("forgot_verify_otp_set_pass.html",data=mail)
        else:
            return render_template("error.html",data="OTP is Invalid")

@app.route('/forgot_verify_otp_set_pass',methods=['GET','POST'])
def forgot_verify_otp_set_pass():
    if request.method=='GET':
        return render_template("forgot_verify_otp_set_pass.html",data="")
    else:
        mail=request.form['email']
        pass1=request.form['pass1']
        pass2=request.form['pass2']
        if pass1==pass2:
            user_data=register_user.objects(email=mail)
            if user_data:
                hash_password=pbkdf2_sha256.using(rounds=8000, salt_size=10).hash(pass1)
                user_data.update(password=hash_password)
                return render_template("success.html",data="Password Updated Successfully")
            else:
                return render_template("error.html",data="User Not Found")       
        else:
            return render_template("error.html",data="Both passwords should be same")       


@app.route('/notifications',methods=['GET','POST'])
def notifications():   
    if request.method=='GET':
        return render_template("notifications.html")
    else:
        msg=request.form['message']
        
        date_time=datetime.datetime.now()
        day=date_time.strftime("%d")
        month=date_time.strftime("%m")
        year=date_time.strftime("%Y")
        time=date_time.strftime("%H")
        min=date_time.strftime("%M")

        t1=time
        t2=min
        time_1=""
        if int(t1)>12:
            t1=str(int(t1)-12)
            time_1=t1+":"+t2+" "+"PM"
        elif int(t1)==12:
            time_1=t1+":"+t2+" "+"PM"
        else:
            time_1=t1+":"+t2+" "+"AM"


        date=day+"/"+month+"/"+year

        '''with mail.connect() as con:
            for user in users:
                msgs = Message(recipients=[user],body = msg+"\n"+"date:"+date+"\n"+"Time:"+time_1, subject = 'New Mail', sender = 'websiteksp.738@gmail.com')
                con.send(msgs)'''
        c=notification(notification=msg,date=date,time=time_1)
        c.save()
        return render_template("success.html",data="Notification sent Successfully ")

@app.route('/register_api',methods=['GET','POST'])
def register_api():
    if request.method=='GET':
        return render_template("thingspeak_admin.html")
    else:
        ts_id=request.form['ts_id']
        api_key=request.form['api']
        #hash_key=pbkdf2_sha256.using(rounds=8000, salt_size=10).hash(api_key)
        c=api_keys(ch_id=ts_id,api_key=api_key)
        c.save()
        return render_template("success.html",data="Registered Successfully")

@app.route('/unit_price',methods=['GET','POST'])
def unit_price():
    if request.method=='GET':
        return render_template("unit_price.html")
    else:
        c=price_of_one_unit.objects()
        rural=request.form['rural']
        urban=request.form['urban']
        fix_r=request.form['fix_r']
        fix_u=request.form['fix_u']

        date_time=datetime.datetime.now()
        day=date_time.strftime("%d")
        month=date_time.strftime("%m")
        year=date_time.strftime("%Y")
        time=date_time.strftime("%H")
        min=date_time.strftime("%M")

        t1=time
        t2=min
        time_1=""
        if int(t1)>12:
            t1=str(int(t1)-12)
            time_1=t1+":"+t2+" "+"PM"
        elif int(t1)==12:
            time_1=t1+":"+t2+" "+"PM"
        else:
            time_1=t1+":"+t2+" "+"AM"


        date=day+"/"+month+"/"+year
        
        c.update(rural_price=rural,
        urban_price=urban,
        fixed_price_rural=fix_r,
        fixed_price_urban=fix_u,
        date=date,
        time=time_1)
            
        #c=price_of_one_unit(rural_price=rural,urban_price=urban,fixed_price_rural=fix_r,fixed_price_urban=fix_u,date=date,time=time_1)
        #c.save()
        return render_template("admin_success.html",data="Price Updated Successfully")


@app.route('/current_status',methods=['GET','POST'])
def current_status():
    m_id=meter_id_cookie[0]
    data1=register_user.objects(meter_id=m_id)
    ts_id=[i.thingspeak_id for i in data1]

    data2=api_keys.objects(ch_id=ts_id[0])
    api=[i.api_key for i in data2]

    full_doc_url="https://api.thingspeak.com/channels/"+ts_id[0]+"/fields/1.json?api_key="+api[0]
    last_entry_url="https://api.thingspeak.com/channels/"+ts_id[0]+"/fields/1/last.json?api_key="+api[0]

    full_doc=urllib.request.urlopen(full_doc_url)
    last_entry=urllib.request.urlopen(last_entry_url)
    
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

    blinks_from_ts=data2['field1']

    time=data2['created_at']
    date=time.replace("Z","")
    date=date.split("T")

    f_date=date[0]
    f_time=date[1]

            #data=register_user.objects(email=email_cookie[0],meter_id=meter_id_cookie[0])
    data=register_user.objects(meter_id=m_id)
        
        
    area=[str(i.area) for i in data]
    area=area[0]

            #return jsonify(area)

    if area=="Rural":
        one_unit_price=4
    else:
        one_unit_price=7
        
    #cost=int((blinks_from_ts)*(one_unit_price/3200))
    kwh=str(int(blinks_from_ts)/3200)
    bill=str(int(blinks_from_ts)*(one_unit_price/3200))

    return render_template("current_status.html",kwh=kwh,bill=bill)




if __name__=="__main__":
    #s=APScheduler()
    #s.add_job(func=main_activity,trigger='interval',id='job',minutes=1)
    #s.start()
    app.run(debug=True)
