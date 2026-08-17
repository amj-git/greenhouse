'''
gh_mqtt.py

Publishes sensor/controller readings to an MQTT broker using Home
Assistant's MQTT Discovery format. Every parameter described via the IO
process's OPDESC? query (see io_thread.py) gets one retained discovery
message and then a state message on every reading - so new sensors show
up in Home Assistant automatically with no per-sensor HA config, the same
"generic from OPDESC" approach the status grid/graphs/web dashboard use.

Read-only / logging integration only - this does not subscribe to any
command topics, so Home Assistant cannot control the greenhouse yet.

dependency: pip install paho-mqtt
'''

import json
import re
from kivy.logger import Logger
from process_control import pr_cont
import paho.mqtt.client as mqtt

CONFIG_FILE = 'mqtt_config.json'

DEFAULT_CONFIG = {
    'enabled': False,
    'host': 'homeassistant.local',
    'port': 1883,
    'username': '',
    'password': '',
    'base_topic': 'greenhouse',
    'discovery_prefix': 'homeassistant',
    'node_id': 'greenhouse',
    'device_name': 'Greenhouse',
}

#Maps io_thread ptype (io_thread.py _set_op_desc()) -> HA sensor device_class
#Anything not listed here is still published, just as a plain numeric sensor
PTYPE_DEVICE_CLASS = {
    'temp': 'temperature',
    'humid': 'humidity',
    'light': 'illuminance',
}


def _slug(text):
    #MQTT topic levels / HA object_ids - keep to [a-z0-9_]
    return re.sub(r'[^a-z0-9_]+', '_', text.strip().lower()).strip('_')


def load_config():
    config = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE) as f:
            config.update(json.load(f))
    except FileNotFoundError:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        Logger.info("gh_mqtt: no %s found - wrote a default (disabled) one" % CONFIG_FILE)
    return config


#START class gh_mqtt-------------------------------------
class gh_mqtt:
    '''
    gio = a started gh_io_dispatcher (this is what fires the on_io_data event)
    io_desc = result of get_all_op_descriptions(): {tname: {pname: {pdesc,ptype,punits,...}}}
    '''
    def __init__(self, gio, io_desc, config=None):
        self._gio = gio
        self._io_desc = io_desc
        self._config = config if config is not None else load_config()
        self._client = None
        self._avail_topic = "%s/status" % self._config['base_topic']

    def start(self):
        if not self._config.get('enabled'):
            Logger.info("gh_mqtt: disabled (see %s) - not connecting" % CONFIG_FILE)
            return
        c = self._config
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=c['node_id'])
        if c.get('username'):
            client.username_pw_set(c['username'], c.get('password') or None)
        client.will_set(self._avail_topic, payload='offline', retain=True)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        self._client = client
        pr_cont.set_name('gh_mqtt')
        try:
            client.connect_async(c['host'], int(c['port']), keepalive=60)
        except Exception as e:
            Logger.exception("gh_mqtt: connect_async(%s:%s) failed: %s" % (c['host'], c['port'], e))
            return
        client.loop_start()  #own network thread; also handles auto-reconnect
        self._gio.bind(on_io_data=self._on_io_data)

    def stop(self):
        if self._client is not None:
            self._client.publish(self._avail_topic, 'offline', retain=True)
            self._client.loop_stop()
            self._client.disconnect()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            Logger.error("gh_mqtt: connection to %s:%s failed: %s" %
                          (self._config['host'], self._config['port'], reason_code))
            return
        Logger.info("gh_mqtt: connected to %s:%s" % (self._config['host'], self._config['port']))
        self._publish_discovery()
        client.publish(self._avail_topic, 'online', retain=True)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        Logger.info("gh_mqtt: disconnected (%s) - will auto-reconnect" % reason_code)

    def _state_topic(self, tname, pname):
        return "%s/%s/%s/state" % (self._config['base_topic'], _slug(tname), _slug(pname))

    #Publishes one retained HA discovery config per (thread,parameter), grouped
    #under a single HA device so they all appear together in the HA UI
    def _publish_discovery(self):
        c = self._config
        device = {
            'identifiers': [c['node_id']],
            'name': c['device_name'],
        }
        for tname, params in self._io_desc.items():
            for pname, desc in params.items():
                object_id = "%s_%s" % (_slug(tname), _slug(pname))
                payload = {
                    'name': "%s %s" % (tname, desc.get('pdesc', pname)),
                    'unique_id': "%s_%s" % (c['node_id'], object_id),
                    'state_topic': self._state_topic(tname, pname),
                    'availability_topic': self._avail_topic,
                    'unit_of_measurement': desc.get('punits') or None,
                    'device_class': PTYPE_DEVICE_CLASS.get(desc.get('ptype')),
                    'state_class': 'measurement',
                    'device': device,
                }
                payload = {k: v for k, v in payload.items() if v is not None}
                config_topic = "%s/sensor/%s/%s/config" % (c['discovery_prefix'], c['node_id'], object_id)
                self._client.publish(config_topic, json.dumps(payload), retain=True)

    #bound to gh_io_dispatcher's on_io_data event - runs on the Kivy main
    #thread (see gh_io_dispatcher._clock_heartbeat), same as every other
    #on_io_data consumer in this codebase
    def _on_io_data(self, *args):
        if self._client is None:
            return
        data = args[1]
        topic = self._state_topic(data['tname'], data['pname'])
        self._client.publish(topic, data['data'], retain=True)
#END class gh_mqtt-------------------------------------
