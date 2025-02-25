import json
import paho.mqtt.client as mqtt
import time

# AWS IoT MQTT Broker Endpoint
MQTT_BROKER = "a12zxwrgxnnoko-ats.iot.ap-south-1.amazonaws.com"
MQTT_PORT = 8883
MQTT_TOPIC = "esp32/sub"

# Certificate paths inside the Lambda deployment package
CERT_PATH = "/var/task/device.pem.crt"
KEY_PATH = "/var/task/private.pem.key"
ROOT_CA_PATH = "/var/task/Amazon-root-CA-1.pem"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

def determine_led_color(user_id):
    user_color_map = {
        'e1d39daa-4011-7062-f606-4ac5a73a3ce4': 'Green',
        '124': 'Yellow'
    }
    return user_color_map.get(user_id, 'default_color')

def determine_led_location(location):
    led_location_map = {
        'H1':'L1',
        'E12':'L2',
        'E13':'L3',
        'E14':'L4',
        'E15':'L5',
        'E16':'L6',
        'E17':'L7'
    }
    return led_location_map.get(location, 'default_location')

def lambda_handler(event, context):
    try:
        # Extract the message from the SNS event
        message = event['Records'][0]['Sns']['Message']
        print(f"Received message: {message}")

        # Parse the message if it's a JSON string
        data = json.loads(message)

        print(data)

        # Extract required fields
        location = determine_led_location(data.get('location'))
        user_id = data.get('userId')  # Fixed: was passing this directly to determine_led_color
        light_status = data.get('light')

        # Determine LED color
        color = determine_led_color(user_id)

        # Determine LED action based on light status
        action = 'ON' if light_status else 'OFF'

        # Construct the message payload - MOVED HERE BEFORE MQTT CONNECTION
        payload = {
            'location': location,
            'color': color,
            'action': action
        }

        # Setup MQTT Client
        client = mqtt.Client()
        client.tls_set(ROOT_CA_PATH, certfile=CERT_PATH, keyfile=KEY_PATH)
        client.on_connect = on_connect

        # Add publish callback
        def on_publish(client, userdata, mid):
            print(f"Message {mid} published successfully")
        client.on_publish = on_publish

        # Connect with error checking
        print("Attempting to connect to MQTT broker...")
        connection = client.connect(MQTT_BROKER, MQTT_PORT, 60)
        if connection != 0:
            raise Exception(f"Connection failed with error code {connection}")

        client.loop_start()
        
        # Wait for connection
        timeout = 5  # seconds
        start_time = time.time()
        while not client.is_connected() and (time.time() - start_time < timeout):
            time.sleep(0.1)
            
        if not client.is_connected():
            raise Exception("Failed to connect to MQTT broker")

        # Publish with QoS 1
        result = client.publish(MQTT_TOPIC, json.dumps(payload), qos=1)
        result.wait_for_publish()
        
        print(f"Published to MQTT topic: {MQTT_TOPIC} with payload: {payload}")
        
        time.sleep(1)
        
        client.loop_stop()
        client.disconnect()

        return {
            'statusCode': 200,
            'body': json.dumps('Message processed and published successfully!')
        }

    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Failed to process message: {str(e)}")
        }