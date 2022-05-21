'''
from flask import Flask,render_template, request
from flask_mysqldb import MySQL
import mysql.connector as mysql
 
app = Flask(__name__)

h="iot-smart-energy-meter.000webhostapp.com"
d="id18875190_iot_smart_energy_meter"
u="id18875190_batch23"
p="QC>-4Vt-)HKWkA@j"

db_connection=mysql.connect(host=h, database=d, user=u, password=p)
print("connected to :",db_connection.get_server_info())
 
app.config['MYSQL_HOST'] = 'iot-smart-energy-meter.000webhostapp.com'
app.config['MYSQL_USER'] = 'id18875190_batch23'
app.config['MYSQL_PASSWORD'] = 'QC>-4Vt-)HKWkA@j'
app.config['MYSQL_DB'] = 'id18875190_iot_smart_energy_meter'
 
mysql = MySQL(app)

 
@app.route("/user")
def user():
    cur = mysql.connection.cursor() 
    cur.execute("""SELECT * FROM `USER_DB` WHERE id = 1""")
    user = cur.fetchall()
    return render_template('user.html', user = user)



if __name__=="__main__":
    app.run(host="0.0.0.0" ,debug=True)

'''

import urllib.request
from flask import Flask,render_template, request,jsonify
import json
import time
from flask_mongoengine import MongoEngine
import requests,random


app = Flask(__name__)


app.config['MONGODB_SETTINGS'] = {
'db': 'IOT_ENERY_METER',
'host': 'localhost',
'port': 27017
}
db = MongoEngine()
db.init_app(app)

import config

api_key=config.api_key
ch_id=config.ch_id




class blinks(db.Document):
    user_id=db.StringField()
    blink_count=db.IntField()
    date = db.StringField()
    time = db.StringField()



@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/', methods=['POST'])
def create_record():
    record = json.loads(request.data)
    c =blinks(user_id=record['id'],
    blink_count=record['blinks_count'],
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
    id=i['id']

    #d=data['feeds']

    blinks=data2['field1']

    time=data2['created_at']
    date=time.replace("Z","")
    date=date.split("T")

    f_date=date[0]
    f_time=date[1]

   # cost=blinks*0.00125

    x={"id":str(id),
        "blinks_count":blinks,
        "f_date":f_date,
        "f_time":f_time,
    }
    x=json.dumps(x)
    response = requests.post(url="https://smart-energy-monitoring.herokuapp.com",data=x)
 
    return jsonify(response.text)



if __name__=="__main__":
    app.run(debug=True)
