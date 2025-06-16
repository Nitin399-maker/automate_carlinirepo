def get_score(response, context=None):
    """
    Test if a model can write upython code with an obscure module.
    Checks for required substrings in MicroPython MQTT code for Raspberry Pi Pico W.
    """
    
    required_substrings = [
        "check_msg",
        "MQTTClient", 
        "set_callback",
        "WLAN",
        "STA_IF"
    ]
    
    # Check if all required substrings are present
    missing_substrings = []
    for substring in required_substrings:
        if substring not in response:
            missing_substrings.append(substring)
    
    # Return score and reason
    if not missing_substrings:
        return {
            "pass": True,
            "score": 1.0,
            "reason": "All required MicroPython MQTT components found: " + ", ".join(required_substrings)
        }
    else:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Missing required components: {', '.join(missing_substrings)}"
        }