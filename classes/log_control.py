from logging import Logger
import time
from pydantic import BaseModel

from classes.heartbeat import HeartBeat


class LogControl(BaseModel):
    class Config: 
        arbitrary_types_allowed = True

    retries:int  = 0
    logger: Logger
    retry_period: float
    max_retries: int
    heartbeat_obj: HeartBeat
    client_name: str

    def reset_retries(self):
        self.retries = 0


    def check_retries(self):
        self.retries += 1
        if self.retries < self.max_retries:
            return
        self.logger.error(f"messageRead - Too many retries for  \"{self.client_name}\".")
        #
        # kill heartbeat thread
        #
        self.heartbeat_obj.exit()
        time.sleep(1)
        exit(-1)