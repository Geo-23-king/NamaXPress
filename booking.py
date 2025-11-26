from datetime import datetime

class Booking:
    def __init__(self,name,pickup,dropoff,status="Pending"):
        self.name = name
        self.pickup = pickup
        self.dropoff = dropoff
        self.time = datetime.now().strftime("%H:%M")
        self.status = status
