from fastapi import FastAPI, WebSocket
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from playsound import playsound
import datetime

app = FastAPI()
scheduler = AsyncIOScheduler()
scheduler.start()
alarm_time = None


async def alarm_goes_off(websocket):
    await websocket.send_json({"type": "alarm_goes_off"})
    playsound(
        "C:\\Users\\USER\\Music\\Music\\AJR\\OK ORCHESTRA (320)\\OK ORCHESTRA CD 1 TRACK 3 (320).mp3")


@app.websocket("/alarm/")
async def alarm(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        if data["type"] == "set_alarm":
            try:
                alarm_time = datetime.datetime.strptime(
                    data["time"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                await websocket.send_json({"type": "error", "message": "Invalid time format, should be YYYY-MM-DD HH:MM:SS"})
                continue
            # Schedule the alarm to go off at the specific time
            scheduler.add_job(alarm_goes_off, 'date',
                              run_date=alarm_time, args=[websocket])
            await websocket.send_json({"type": "set_alarm", "message": f"Alarm set for {alarm_time}"})
        elif data["type"] == "snooze":
            if alarm_time is None:
                await websocket.send_json({"type": "error", "message": "No alarm is currently set."})
                continue
            # Set the snooze time to 10 minutes from the current time
            snooze_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
            scheduler.remove_job(alarm_goes_off)
            scheduler.add_job(alarm_goes_off, 'date',
                              run_date=snooze_time, args=[websocket])
            await websocket.send_json({"type": "snooze", "message": f"Alarm snoozed for {snooze_time}"})
        elif data["type"] == "stop_alarm":
            scheduler.remove_all_jobs()
            await websocket.send_json({"type": "stop_alarm", "message": "Alarm stopped"})
            websocket.close()
