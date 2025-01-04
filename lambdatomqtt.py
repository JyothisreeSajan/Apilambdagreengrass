import json
import ssl
import paho.mqtt.client as mqtt
import logging
import requests  # Add this import for API calls

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# MQTT Configuration
MQTT_BROKER = "a12zxwrgxnnoko-ats.iot.ap-south-1.amazonaws.com"
MQTT_PORT = 8883
MQTT_TOPIC = "esp32/command"

# API Configuration
API_URL = "https://main.d3h25u4rwoulnt.amplifyapp.com/api/my-picks/b143edda-1011-7053-4c5e-f5f0475de136/count"

def fetch_api_data():
    """Fetch data from the API endpoint."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Raise exception for non-200 status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching API data: {e}")
        raise

def publish_message(client, message):
    """Publish a message and wait for confirmation."""
    # Variable to track publish success
    publish_complete = False
    
    def on_publish(client, userdata, mid):
        nonlocal publish_complete
        publish_complete = True
        logger.info(f"Message {mid} published successfully")
    
    try:
        # Set up callback for publish confirmation
        client.on_publish = on_publish
        
        # Publish message
        logger.info(f"Publishing message: {message}")
        result = client.publish(MQTT_TOPIC, message, qos=1)
        
        # Wait briefly for publication (max 2 seconds)
        retry = 0
        while not publish_complete and retry < 20:
            client.loop(0.1)  # 100ms loop
            retry += 1
        
        if not publish_complete:
            raise Exception("Publication timeout")
            
        return True
        
    except Exception as e:
        logger.error(f"Error publishing message: {e}")
        raise

def lambda_handler(event, context):
    try:
        # Fetch data from API
        api_data = fetch_api_data()
        logger.info(f"Received API data: {api_data}")

        # Create MQTT client with unique ID
        client = mqtt.Client(client_id="lambda_test_publisher")
        
        # Configure TLS/SSL
        client.tls_set(
            ca_certs="Amazon-root-CA-1.pem",
            certfile="device.pem.crt",
            keyfile="private.pem.key",
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        
        # Connect to broker
        logger.info(f"Connecting to {MQTT_BROKER}")
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        
        # Publish API data
        publish_message(client, json.dumps(api_data))
        
        # Clean disconnect
        client.disconnect()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'API data published successfully',
                'topic': MQTT_TOPIC,
                'payload': api_data
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda function: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to publish message',
                'details': str(e)
            })
        }