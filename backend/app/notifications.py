"""Push notification service for triggering incoming call UI on mobile apps"""

import json
from typing import Optional
from app.config import settings

# Firebase Admin SDK (optional - gracefully handle if not configured)
firebase_app = None

def init_firebase():
    """Initialize Firebase Admin SDK if credentials are available"""
    global firebase_app
    try:
        import firebase_admin
        from firebase_admin import credentials
        import os
        
        if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_app = firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized")
        else:
            print(f"Firebase credentials not found at {settings.FIREBASE_CREDENTIALS_PATH}")
            print("Push notifications will be disabled")
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        print("Push notifications will be disabled")


async def send_call_notification(
    device_token: str,
    device_platform: str,
    session_id: str,
    session_type: str,
    caller_name: str = "Calla",
    metadata: dict = None
) -> Optional[str]:
    """
    Send high-priority push notification that triggers incoming call UI.
    
    On Android: Use FCM with high priority + call channel
    On iOS: Use VoIP push (requires special certificate) or regular push with CallKit
    
    Returns message ID if successful, None if failed
    """
    if firebase_app is None:
        print("Firebase not initialized, skipping push notification")
        return None
    
    try:
        from firebase_admin import messaging
        
        data_payload = {
            "type": "incoming_call",
            "session_id": session_id,
            "session_type": session_type,
            "caller_name": caller_name,
            "metadata": json.dumps(metadata or {}),
        }
        
        if device_platform == "android":
            message = messaging.Message(
                token=device_token,
                android=messaging.AndroidConfig(
                    priority="high",
                    ttl=60,  # 60 seconds TTL
                    notification=messaging.AndroidNotification(
                        channel_id="incoming_calls",
                        title="Incoming Call",
                        body=f"{caller_name} is calling...",
                        sound="ringtone",
                        priority="max",
                        visibility="public",
                        default_vibrate_timings=False,
                        vibrate_timings_millis=[0, 500, 200, 500],
                    ),
                ),
                data=data_payload
            )
        else:  # iOS
            message = messaging.Message(
                token=device_token,
                apns=messaging.APNSConfig(
                    headers={
                        "apns-priority": "10",
                        "apns-expiration": "60",
                        # For VoIP, use "apns-push-type": "voip" with VoIP certificate
                        "apns-push-type": "alert",
                    },
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title="Incoming Call",
                                body=f"{caller_name} is calling...",
                            ),
                            sound=messaging.CriticalSound(
                                name="ringtone.caf",
                                critical=True,
                                volume=1.0
                            ),
                            category="INCOMING_CALL",
                            mutable_content=True,
                        ),
                    ),
                ),
                data=data_payload
            )
        
        response = messaging.send(message)
        print(f"Push notification sent: {response}")
        return response
    
    except Exception as e:
        print(f"Failed to send push notification: {e}")
        return None


async def send_missed_call_notification(
    device_token: str,
    device_platform: str,
    caller_name: str = "Calla",
    message: str = "You missed a medication reminder call"
) -> Optional[str]:
    """Send a regular notification for missed calls"""
    if firebase_app is None:
        return None
    
    try:
        from firebase_admin import messaging
        
        msg = messaging.Message(
            token=device_token,
            notification=messaging.Notification(
                title=f"Missed Call from {caller_name}",
                body=message,
            ),
            data={
                "type": "missed_call",
                "caller_name": caller_name,
            }
        )
        
        response = messaging.send(msg)
        return response
    except Exception as e:
        print(f"Failed to send missed call notification: {e}")
        return None

