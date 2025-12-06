# Natural Language Conversations with Gemini Live

## Overview

The Calla platform uses **Gemini 2.0 Flash Live API** for natural voice conversations with patients. Instead of pressing buttons, patients can speak naturally like they would to a person.

## Architecture

```
Patient Phone ←→ Twilio ←→ Backend WebSocket ←→ Gemini Live API
                    ↓
           (Audio Conversion)
           mulaw 8kHz ↔ PCM 16kHz
```

### Audio Flow

1. **Patient speaks** → Phone captures audio
2. **Twilio** → Sends mulaw 8kHz audio via WebSocket (Media Streams)
3. **Backend** → Converts mulaw → PCM 16-bit 16kHz
4. **Gemini Live** → Processes audio, understands natural language
5. **Gemini** → Responds with voice (PCM 16kHz)
6. **Backend** → Converts PCM → mulaw 8kHz
7. **Twilio** → Plays audio to patient

## Natural Language Understanding

### What Patients Can Say

**To confirm medication:**
- "Yes"
- "I took it"
- "Already did"
- "Of course"
- "Just took it now"
- "Yep, all done"

**To request more time:**
- "Not yet"
- "I need more time"
- "I forgot"
- "Can you call me back?"
- "I'll take it in a few minutes"

**If confused:**
- "Who is this?"
- "What medication?"
- "I don't understand"

→ Gemini will explain it's their medication reminder system

### How Gemini Understands

Gemini uses the existing "reminder" prompt from `backend/app/voice/gemini_voice.py`:

```
You're reminding {{patient_name}} to take their {{medication_name}} ({{dosage}}).

Your goals:
1. Greet them warmly by name
2. Remind them it's time for their medication
3. Confirm whether they've taken it
4. If not taken, gently encourage them
5. Keep the call brief (under 2 minutes)
```

The prompt instructs Gemini to output structured JSON:
```json
{
  "medication_taken": true/false,
  "reason_not_taken": "reason if not taken",
  "needs_refill": true/false,
  "escalate_to_caregiver": true/false
}
```

## Technical Implementation

### Key Files

| File | Purpose |
|------|---------|
| `backend/app/twilio_service.py` | Initiates Twilio calls with Media Streams |
| `backend/app/voice/twilio_stream_handler.py` | Bridges Twilio ↔ Gemini Live |
| `backend/app/voice/gemini_voice.py` | Gemini Live API integration |
| `backend/app/voice/router.py` | WebSocket endpoint for Twilio streams |

### Audio Conversion

**Twilio Format:**
- Codec: mulaw (8-bit)
- Sample rate: 8kHz
- Channels: mono

**Gemini Format:**
- Codec: PCM 16-bit
- Sample rate: 16kHz
- Channels: mono

**Conversion Functions:**
```python
def _convert_mulaw_to_pcm16(mulaw_data: bytes) -> bytes:
    # Decode mulaw to PCM
    pcm_8khz = audioop.ulaw2lin(mulaw_data, 2)
    # Upsample to 16kHz
    pcm_16khz, _ = audioop.ratecv(pcm_8khz, 2, 1, 8000, 16000, None)
    return pcm_16khz

def _convert_pcm16_to_mulaw(pcm_data: bytes) -> bytes:
    # Downsample to 8kHz
    pcm_8khz, _ = audioop.ratecv(pcm_data, 2, 1, 16000, 8000, None)
    # Encode to mulaw
    mulaw = audioop.lin2ulaw(pcm_8khz, 2)
    return mulaw
```

### WebSocket Protocol

**Twilio → Backend:**
```json
{
  "event": "start",
  "start": {
    "streamSid": "MZ123...",
    "callSid": "CA123..."
  }
}
```

```json
{
  "event": "media",
  "media": {
    "payload": "base64_encoded_mulaw_audio"
  }
}
```

```json
{
  "event": "stop"
}
```

**Backend → Twilio:**
```json
{
  "event": "media",
  "streamSid": "MZ123...",
  "media": {
    "payload": "base64_encoded_mulaw_audio"
  }
}
```

## Example Conversation

### Scenario: Patient Answers Call

```
📞 Call initiated at 8:00 AM

Gemini: "Hello Mary, this is Calla, your medication reminder.
         It's time to take your Lisinopril, 10 milligrams.
         Have you taken it yet?"

Patient: "Oh yes, I took it about 10 minutes ago."

Gemini: "Wonderful! Thank you for taking care of yourself, Mary.
         Have a great day!"

✓ Call ends
✓ Reminder marked as "confirmed"
✓ Adherence event logged: "Natural language confirmation. Transcript: Hello Mary ... Oh yes, I took it ..."
```

### Scenario: Patient Needs More Time

```
📞 Call initiated at 8:00 AM

Gemini: "Hello John, this is Calla. It's time for your Metformin,
         500 milligrams. Have you taken it?"

Patient: "Not yet, I'm still eating breakfast."

Gemini: "That's perfectly fine, John. Make sure to take it when you finish.
         I'll call you back in a few minutes to check in. Take care!"

✓ Call ends
⏰ Status remains "calling" for retry
⏰ 3 minutes later: Call again
```

### Scenario: Patient Is Confused

```
📞 Call initiated

Gemini: "Hello Sarah, this is Calla—"

Patient: "Who is this? How did you get my number?"

Gemini: "I'm Calla, your automated medication reminder system.
         Your caregiver set this up to help you remember your medications.
         I'm calling to remind you it's time for your Atorvastatin."

Patient: "Oh! Right, the reminder thing. Yes, I took it."

Gemini: "Great! Thank you for confirming, Sarah."

✓ Call ends, confirmed
```

## Customization

### Voice Selection

Change the Gemini voice in `backend/app/voice/twilio_stream_handler.py`:

```python
config = gemini_voice_service.create_session_config(
    session_type="reminder",
    variables={...},
    voice_name="Aoede"  # Options: Puck, Charon, Kore, Fenrir, Aoede
)
```

### Prompt Customization

Edit prompts in `backend/app/voice/gemini_voice.py`:

```python
AGENT_PROMPTS = {
    "reminder": """
    You are Calla, a friendly medication reminder assistant.

    [Your custom instructions here]
    """
}
```

## Debugging

### View Conversation Logs

Check backend logs for transcripts:
```bash
docker logs calla_backend | grep "Gemini:"
```

Example output:
```
INFO: Gemini: Hello Mary, it's time to take your Lisinopril...
INFO: Gemini: Wonderful! Thank you for taking care of yourself...
INFO: Patient confirmed medication for reminder abc-123
```

### Test Twilio Media Streams

1. Check Twilio console → Logs → Calls
2. Look for "Stream Connected" events
3. Verify audio is flowing both ways

### Common Issues

| Issue | Solution |
|-------|----------|
| "No audio from Gemini" | Check Gemini API key, verify GEMINI_LIVE_MODEL is correct |
| "Patient can't hear me" | Verify PCM→mulaw conversion, check Twilio stream status |
| "Gemini doesn't understand" | Review prompt in gemini_voice.py, test with clearer speech |
| "WebSocket connection fails" | Ensure backend has public wss:// URL, check ngrok |

## Cost Considerations

**Twilio Media Streams:**
- ~$0.013/minute for voice calls (US)
- Real-time audio streaming included

**Gemini 2.0 Flash Live API:**
- Check current pricing at https://ai.google.dev/pricing
- Typically charged per audio minute

**Example cost for 100 patients:**
- 100 patients × 3 calls/day × 1 min/call × $0.013 = ~$3.90/day
- Plus Gemini API costs
- Total: ~$120-150/month estimated

## Benefits of Natural Language

1. ✅ **More natural** - Patients speak normally, no button pressing
2. ✅ **Better for elderly** - Many can't see buttons or have dexterity issues
3. ✅ **Conversation context** - Gemini can handle follow-up questions
4. ✅ **Rich data** - Transcripts provide insight into patient behavior
5. ✅ **Flexibility** - Can handle unexpected responses gracefully

## Limitations

1. ⚠️ **Accent/dialect issues** - Gemini may struggle with strong accents
2. ⚠️ **Background noise** - Phone quality and environment affect recognition
3. ⚠️ **Latency** - ~500ms-2s delay between speech and response
4. ⚠️ **Cost** - Higher than simple IVR systems
5. ⚠️ **Requires internet** - Backend must be online for Gemini API calls

## Future Enhancements

1. 🔮 **Multi-language** - Support Spanish, Chinese, etc.
2. 🔮 **Emotion detection** - Detect if patient sounds distressed
3. 🔮 **Personalization** - Learn patient's speech patterns over time
4. 🔮 **Side effect reporting** - "I'm feeling dizzy from this medication"
5. 🔮 **Refill management** - "I'm running low, can you order more?"

---

**Last updated:** 2025-12-06
