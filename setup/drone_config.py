import os
from flask import Flask,request,Response
app = Flask(__name__)

snoopyPath=os.path.dirname(os.path.realpath(__file__))
os.chdir(snoopyPath)
settings_file="/etc/init/SETTINGS"

@app.route('/')
def m():
    return "Try /get_config or /set_sensor_id or /logs or /restart_snoopy or /poweroff"

@app.route('/get_config')
def gc():
    try:
        lines=open(settings_file, 'r').read()
    except:
        return "Unable to open %s. Have you copied the upstart scripts over yet?" % settings_file
    return Response(lines, mimetype='text')

@app.route('/set_sensor_id')
def set_sensor_id():
    sensor_id = request.args.get('id', None)
    if not sensor_id:
        return "Please pass sensor_id number as a GET paramter to set it. e.g. /set_sensor_id/?id=101"
    try:
        sensor_id=int(sensor_id)
    except:
        return "Please pass sensor_id *number* as a GET paramter to set it. e.g. /set_sensor_id/?id=101"
    newlines=[]    

    lines=open(settings_file, 'r').readlines()
    for line in lines:
        line=line.strip()
        if line.startswith("drone_num="):
            line = "drone_num=%s" % sensor_id
        elif line.startswith("remote_base_port="):
            base_port=int(line[17:])
        newlines.append(line)
    f=open(settings_file, 'w')
    for line in newlines:
        print>>f, line
    return "Set sensor_id to 'sensor%s', and remote SSH listening port to %d"%(sensor_id,base_port+sensor_id)

@app.route('/poweroff')
def po():
    stdin,stdout = os.popen2("poweroff")
    return "Powering down..."

@app.route('/restart_snoopy')
def rs():
    stdin,stdout = os.popen2("service snoopy restart")
    stdin,stdout = os.popen2("service phone_home restart")
    return "Restarting Snoopy..."

@app.route('/logs')
def logs():
    lines = tail('/home/ubuntu/snoopy_ng/snoopy.log', 80)
    if lines:
        return Response(lines, mimetype='text')
    else:
        return "No log file found"

def tail(f, n):
  #stdin,stdout = os.popen2("tail -n %s %s" % (n,f))
  stdin,stdout = os.popen2("cat /var/log/syslog | grep sng_ | tail -n 50")
  stdin.close()
  lines = stdout.readlines(); stdout.close()
  lines = ''.join(lines)
  return lines

if __name__ == '__main__':
    app.debug=True
    app.run(host="0.0.0.0")
