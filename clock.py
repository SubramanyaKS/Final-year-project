from app import register_user,api_keys,blinks
from apscheduler.schedulers.blocking import BlockingScheduler
from flask_mongoengine import MongoEngine
import urllib.request
import json


s=BlockingScheduler()
#@app.route('/main')
@s.scheduled_job('interval',minutes=1)
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
            response = requests.post(url="http://127.0.0.1:5000/",data=x)
    
            return response.text"""
            c = blinks(user_id=str(ts_id),
            blink_count= blinks_from_ts,
            meter_id=m_id,
            price=cost,
            date=f_date,
            time=f_time)        
            c.save()

s.start()   