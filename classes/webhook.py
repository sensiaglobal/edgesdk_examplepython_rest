from logging import Logger
from threading import Thread
import time
import queue
from typing import List
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel
import uvicorn

from classes.api_classes import MessageOutboundInterchange, MessageReadAdvancedResp
from config.appconfig import AppConfig
from lib.webhookfuncs import enqueue

class WebHook (BaseModel):
    logger: Logger
    queue:queue.Queue
    config:AppConfig
    host:str = ""
    suffix:str = ""
    protocol:str = ""
    port:int = 0

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self.host = self.config.wh.host
        self.suffix = self.config.wh.suffix
        self.protocol = self.config.wh.protocol
        self.port = self.config.wh.port

    def start(self):
          
        thread = Thread(target=self.run)
        thread.start()
        return
    
    def run(self):
        self.webhook_mgr()
        self.logger.warning(f"Webhook tread ENDED.")

    def webhook_mgr(self):

        app = FastAPI(title="Webhook API")
        test_command = self.suffix + self.config.wh.test.command
        single_message_command = self.suffix + self.config.wh.simple_message.command
        set_of_messages_command = self.suffix + self.config.wh.set_of_messages.command
        advanced_messages_command = self.suffix + self.config.wh.advanced_messages.command

        @app.api_route(test_command, methods=[self.config.wh.test.operation], tags=[self.config.wh.group_tag], status_code=status.HTTP_200_OK)
        async def test(response: Response):
            response.status_code = status.HTTP_200_OK
            return

        @app.api_route(single_message_command,  methods=[self.config.wh.simple_message.operation], tags=[self.config.wh.group_tag], status_code=status.HTTP_200_OK)          
        async def simple_message(payload: MessageOutboundInterchange, response: Response):

            try:
                #
                # Queue the record
                # 
                data = enqueue(self.queue, payload)
                return {"status": "OK"}

            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal Server Error. Message: " + str(e))
    
        @app.api_route(set_of_messages_command,  methods=[self.config.wh.set_of_messages.operation], tags=[self.config.wh.group_tag], status_code=status.HTTP_200_OK)          
        async def set_of_message(payload: MessageOutboundInterchange, response: Response):
            try:
                #
                # Queue the record
                # 
                data = enqueue(self.queue, payload)
                return {"status": "OK"}

            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal Server Error. Message: " + str(e))

        @app.api_route(advanced_messages_command,  methods=[self.config.wh.advanced_messages.operation], tags=[self.config.wh.group_tag], status_code=status.HTTP_200_OK)          
        async def advanced_message(payload: MessageReadAdvancedResp, response: Response):      
            try:
                #
                # Queue the record
                # 
                data = enqueue(self.queue, payload)
                return {"status": "OK"}

            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal Server Error. Message: " + str(e))


        uvicorn.run(app, host=self.host, port=self.port, log_level=self.config.log.api_level.lower())



