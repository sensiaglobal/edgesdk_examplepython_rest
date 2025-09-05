from threading import Thread
import time
import queue

class HeartBeat (object):
    def __init__(self, logger, client, dq, initial_state, period):
        self.logger = logger
        self.client = client
        self.dq = dq
        self.initial_state = initial_state
        self.period = period
        self.running = True

    def start(self):
        thread = Thread(target=self.run)
        thread.start()
        self.logger.debug("Heartbeat Thread started.")
        return True

    def run(self):
        #
        # Send the heart beat (false for  the first time)
        #
        up = self.initial_state

        while self.running:
            try:
                up = self.dq.get(block=False)
            except queue.Empty:
                pass    
            try:   
                response = self.client.heartbeatApp(up=up)
            except Exception as e:
                self.logger.error(f"Error trying to send Heartbeat. Error: {e}")             
            time.sleep(self.period)
        return
    
    def change_state (self, new_state):
        self.dq.put(new_state)
        return
    
    def exit (self):
        self.running = False
        return