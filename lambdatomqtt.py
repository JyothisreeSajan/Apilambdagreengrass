import json
import os
import requests
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER = "a12zxwrgxnnoko-ats.iot.ap-south-1.amazonaws.com"
MQTT_TOPIC = "esp32/command"
CERTS_DIR = "/path/to/certs"  # Update to the directory containing your certificate files
CA_CERT = os.path.join(CERTS_DIR, "AmazonRootCA1.pem")
CERT_FILE = os.path.join(CERTS_DIR, "device.pem.crt")
KEY_FILE = os.path.join(CERTS_DIR, "private.pem.key")

def publish_to_mqtt(data):
    """Publish data to the MQTT topic."""
    try:
        # Create MQTT client
        client = mqtt.Client()
        
        # Configure TLS/SSL for MQTT connection
        client.tls_set(ca_certs=CA_CERT, certfile=CERT_FILE, keyfile=KEY_FILE)
        
        # Connect to MQTT Broker
        client.connect(MQTT_BROKER, 8883)
        
        # Publish the message
        payload = json.dumps(data)  # Ensure data is in JSON format
        client.publish(MQTT_TOPIC, payload)
        print(f"Published to MQTT Topic '{MQTT_TOPIC}': {payload}")
        
        # Disconnect after publishing
        client.disconnect()
    except Exception as e:
        print(f"Error publishing to MQTT: {e}")
        raise

def lambda_handler(event, context):
    # API configuration
    api_base_url = os.environ.get('API_BASE_URL', 'https://main.d3h25u4rwoulnt.amplifyapp.com/api')  # Default to local API
    
    try:
        # Fetch new order details from the API
        response = requests.get(f"{api_base_url}/my-picks/b143edda-1011-7053-4c5e-f5f0475de136/count")  # Adjust the endpoint as needed
        
        # Check if the API call was successful
        if response.status_code == 200:
            new_orders = response.json()  # Assuming the API returns JSON data
            print(f"Retrieved orders: {new_orders}")
            
            # Publish orders to MQTT topic
            publish_to_mqtt(new_orders)
        else:
            print(f"Failed to fetch orders: {response.status_code} - {response.text}")
            return {
                'statusCode': response.status_code,
                'body': f"Error: {response.text}"
            }
    
    except Exception as e:
        print(f"Error fetching orders from API: {e}")
        return {
            'statusCode': 500,
            'body': f"Internal server error: {str(e)}"
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps("Orders processed and published successfully.")
    }
