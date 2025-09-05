#
# Copyright (c) 2025 Sensia Global
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#  
# Python client interface for HCC2 SDK 2.0
#
from datetime import datetime, timedelta
import json
import os
from typing import List
from pydantic import BaseModel, TypeAdapter, field_validator
import requests
from http import HTTPStatus

from classes.enums import quality_enum
from config.apiconfig import ApiConfig, Ops
from lib.miscfuncs import convert_datetime_to_UTC, convert_datetime_to_unix_time

class MessageHeatbeatReq(BaseModel):
    isUp: bool

class MessageCheckStatusResp(BaseModel):
    hasNewConfig: bool

class MessageValidateStatusReq(BaseModel):
    isValid: bool

class TvqtDataPoint(BaseModel):
    topic: str
    value: object
    quality: quality_enum
    timeStamp: datetime

    @field_validator('quality', mode='after')
    def convert_quality(cls, value):
        if isinstance(value, quality_enum):
            return value.value
        return value

    @field_validator('timeStamp', mode='after')
    def convert_timeStamp(cls, value):
        if isinstance(value, datetime):
            return str(convert_datetime_to_unix_time(convert_datetime_to_UTC(value))) + "000" # to microseconds
        return value

    @classmethod
    def _from_response(cls, response):
        return TvqtDataPoint(response.topic, response.value, response.quality, response.datetime)

class SetDatapoint(BaseModel):
    dataPointName: str
    quality: int 
    timeStamps: list[str]
    values: list[object]

    @field_validator('quality', mode='after')
    def convert_quality(cls, value):
        if isinstance(value, quality_enum):
            return value.value
        return value

    @field_validator('timeStamps', mode='before')
    def convert_timeStamps(cls, value):
        if isinstance(value, list) and all(isinstance(i, datetime) for i in value):
            return [str(convert_datetime_to_unix_time(i)) + "000" for i in value]
        return value

class GetDatapoint(BaseModel):
    dataPointName: str
    quality: int 
    timeStamps: list[str]
    values: list[object]

    @field_validator('quality', mode='after')
    def convert_quality(cls, value):
        if isinstance(value, int):
            return quality_enum(value)
        return value

    @field_validator('timeStamps', mode='after')
    def convert_timeStamps(cls, value):
        if all(isinstance(i, str) for i in value):
            newvals=[]
            for val in value:
                seconds = int(val[:-6])
                microseconds = int(val[-6:])
                val = datetime.fromtimestamp(seconds) + timedelta(microseconds=microseconds)
                newvals.append(val)
            return newvals
        return value

class MessageOutboundInterchange(BaseModel):
    topic: str = ""
    value:object = {}
    msgSource: str = ""
    quality: int = 0
    timeStamp: str = ""

    @field_validator('quality', mode='after')
    def convert_quality(cls, value):
        if isinstance(value, int):
            return quality_enum(value)
        return value

    @field_validator('timeStamp', mode='after')
    def convert_timeStamp(cls, value):
        if isinstance(value, str):
            seconds = int(value[:-6])
            microseconds = int(value[-6:])
            return (datetime.fromtimestamp(seconds) + timedelta(microseconds=microseconds))
        return value

class MessageReadReq (BaseModel):
    topics: list[str] = []
    includeOptional: bool = True

class MessageReadResp (MessageOutboundInterchange):
    pass

class SetOfMessageReadReq (MessageReadReq):
    callbackAPi: str = ""
    includeOptional: bool = True

class AdvancedMessageReadReq (MessageReadReq):
    callbackAPi: str = ""

class MessageReadAdvancedReq (BaseModel):
    topics: list[str] = []

class MessageReadAdvancedResp (BaseModel):
    topic: str
    msgSource: str
    datapoints: list[GetDatapoint]

class MessageWriteReq(MessageOutboundInterchange):
    def __init__(self, topic, value, msgSource, quality, timestamp):
        super().__init__()
        self.topic = topic
        self.value = value
        self.msgSource = msgSource
        self.quality = quality
        self.timeStamp = str(timestamp)

class MessageWriteAdvancedReq (BaseModel):
    topic: str
    msgSource: str
    datapoints: list[SetDatapoint]

class MessageWriteReqVar(BaseModel):
    name: str
    value: object

class MessageWriteAdvancedReqVar(BaseModel):
    name: str
    value: object

class APIBase (BaseModel):
    url: str = ""
    headers: str = ""
    payload: str = ""
    headers: str = ""
    operation: str = ""

    def Build_url(self, api_url, api_suffix):
        self.url = "{0}{1}".format(api_url, api_suffix)
    
    def Build_suffix (api_function):
        pass 
        
    def Build_headers(self, content_type, headers):
        self.headers = { content_type: headers }

    def Build_payload(self):
        pass

    def Request(self):
        pass

class APIInitializeApplication(APIBase):
    
    def Build_suffix(self, app_name):
        return Ops.messageInitializeApplication.suffix.format(app_name)

    def Request(self, app_name:str, cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.messageInitializeApplication.command)
        self.url += self.Build_suffix(app_name)
        
        self.Build_headers("accept", "text/plain")
        self.operation = Ops.messageInitializeApplication.method
        data_response  = requests.request(method=self.operation, url=self.url, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        return data_response.ok

class APIRegisterApplication(APIBase):

    files: dict = {}

    def Build_suffix(self, app_name, is_complex_provisioned):
        return Ops.messageRegisterApplication.suffix.format(app_name, is_complex_provisioned)

    def Build_fileload(self, tarfile_path:str):
        file_name = os.path.basename(tarfile_path)
        fh = open(tarfile_path,'rb')
        self.files = {'formFile':(file_name, fh, 'application/gzip')}
        return fh
        
    def Request(self, app_name:str, tarfile_path:str, is_complex_provisioned: bool, cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.messageRegisterApplication.command)
        self.url += self.Build_suffix(app_name, is_complex_provisioned)
        self.payload = {}
        fh = self.Build_fileload(tarfile_path)
        self.operation = Ops.messageRegisterApplication.method
        data_response  = requests.request(method=self.operation, url=self.url, data=self.payload, files=self.files, timeout=cfg.api_timeout)
        fh.close()
        data_response.raise_for_status()
        return data_response.ok

class APIHeartbeatApplication(APIBase):

    def Build_suffix(self, app_name):
        return Ops.messageHeartbeatApplication.suffix.format(app_name)

    def Build_payload(self, up):
        pl = MessageHeatbeatReq(isUp=up)
        self.payload = pl.model_dump_json()

    def Request(self, app_name:str, up: bool, cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.messageHeartbeatApplication.command)
        self.url += self.Build_suffix(app_name)
        
        self.Build_headers("Content-Type", "application/json")
        self.Build_payload(up)
        self.operation = Ops.messageHeartbeatApplication.method
        data_response  = requests.request(method=self.operation, url=self.url, data=self.payload, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        return data_response.ok

class APICheckProvision(APIBase):
     
    def Build_suffix(self, app_name):
        return Ops.messageCheckProvision.suffix.format(app_name)

    def Request(self, app_name:str, cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.messageCheckProvision.command)
        self.url += self.Build_suffix(app_name)
        
        self.Build_headers("Content-Type", "application/json")
        self.operation = Ops.messageCheckProvision.method
        data_response  = requests.request(method=self.operation, url=self.url, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        message_response_adapter = TypeAdapter(MessageCheckStatusResp)
        response = message_response_adapter.validate_python(data_response.json())
        return response

class APIValidateProvision(APIBase):
    def Build_suffix(self, app_name):
        return Ops.messageValidateProvision.suffix.format(app_name)

    def Build_payload(self, valid: bool):
        pl = MessageValidateStatusReq(isValid=valid)
        self.payload = pl.model_dump_json()

    def Request(self, app_name:str, valid:bool, cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.messageValidateProvision.command)
        self.url += self.Build_suffix(app_name)
        
        self.Build_headers("Content-Type", "application/json")
        self.Build_payload(valid)
        self.operation = Ops.messageValidateProvision.method
        data_response  = requests.request(method=self.operation, url=self.url, data=self.payload, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        return data_response.ok

class APIExtractConfiguration(APIBase):
     
    def Build_suffix(self, app_name):
        return Ops.messageExtractConfiguration.suffix.format(app_name)

    def Request(self, app_name:str, tarball_file_path: str, cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.messageExtractConfiguration.command)
        self.url += self.Build_suffix(app_name)
        
        self.Build_headers("Content-Type", "application/gzip")
        self.operation = Ops.messageExtractConfiguration.method
        data_response  = requests.request(method=self.operation, url=self.url, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        if data_response.status_code == HTTPStatus.OK:
            with open(tarball_file_path, 'wb') as file:
                file.write(data_response.content)
        return data_response.ok

class APICreateGeneralDataPoints(APIBase):
    def Build_suffix(self):
        return Ops.messageCreateGeneralDatapoints.suffix

    def Build_payload(self, topics:list[str]):
        pl = MessageReadReq()
        pl.topics = topics
        pl.includeOptional = True
        self.payload = pl.model_dump_json()

    def Request(self, topics: list[str], cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.messageCreateGeneralDatapoints.command)
        self.url += self.Build_suffix()
        
        self.Build_headers("Content-Type", "application/json")
        self.Build_payload(topics)
        self.operation = Ops.messageCreateGeneralDatapoints.method
        data_response  = requests.request(method=self.operation, url=self.url, data=self.payload, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        message_response_adapter = TypeAdapter(List[MessageReadResp])
        self.response_array = message_response_adapter.validate_python(data_response.json())
        return self.response_array


class APIMessageRead (APIBase):
    response_array: list[MessageReadResp] = []

    def Build_suffix(self):
        return Ops.messageRead.suffix

    def Build_payload(self, topics:list[str]):
        pl = MessageReadReq()
        pl.topics = topics
        pl.includeOptional = True
        self.payload = pl.model_dump_json()

    def Request(self, topics: list[str], cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.messageRead.command)
        self.url += self.Build_suffix()
        
        self.Build_headers("Content-Type", "application/json")
        self.Build_payload(topics)
        self.operation = Ops.messageRead.method
        data_response  = requests.request(method=self.operation, url=self.url, data=self.payload, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        message_response_adapter = TypeAdapter(List[MessageReadResp])
        self.response_array = message_response_adapter.validate_python(data_response.json())
        return self.response_array

class APIMessageReadAdvanced (APIBase):
    response_array: list[MessageReadAdvancedResp] = []

    def Build_suffix(self):
        return Ops.messageReadAdvanced.suffix

    def Build_payload(self, topics:list[str]):
        pl = MessageReadAdvancedReq()
        pl.topics = topics
        self.payload = pl.model_dump_json()

    def Request(self, topics: list[str], cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.messageReadAdvanced.command)
        self.url += self.Build_suffix()
        
        self.Build_headers("Content-Type", "application/json")
        self.Build_payload(topics)
        self.operation = Ops.messageReadAdvanced.method
        data_response  = requests.request(method=self.operation, url=self.url, data=self.payload, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        message_response_adapter = TypeAdapter(List[MessageReadAdvancedResp])
        self.response_array = message_response_adapter.validate_python(data_response.json())
        return self.response_array

class APIMessageWrite (APIBase):
    pass

    def Build_suffix(self):
        return Ops.messageWrite.suffix

    def Build_payload(self, tvqt_list:list[TvqtDataPoint], cfg:ApiConfig):
        pl_array = []
        for tvqt in tvqt_list:
            pl = MessageWriteReq(tvqt.topic, tvqt.value, cfg.api_msg_source, tvqt.quality, tvqt.timeStamp)
            pl_array.append(pl)
        self.payload = json.dumps([pl.dict() for pl in pl_array])

    def Request(self, tqvt_list: list[TvqtDataPoint], cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.messageWrite.command)
        self.url += self.Build_suffix()
        
        self.Build_headers("Content-Type", "application/json")
        self.Build_payload(tqvt_list, cfg)
        self.operation = Ops.messageWrite.method
        data_response  = requests.request(method=self.operation, url=self.url, data=self.payload, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        return data_response.ok

class APIMessageWriteAdvanced (APIBase):

    def Build_suffix(self):
        return Ops.messageWriteAdvanced.suffix

    def Build_payload(self, cdp_list:list[MessageWriteAdvancedReq]):
        self.payload = json.dumps([cdp.model_dump(mode='json') for cdp in cdp_list])

    def Request(self, cdp_list:list[MessageWriteAdvancedReq], cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.messageWriteAdvanced.command)
        self.url += self.Build_suffix()
        
        self.Build_headers("Content-Type", "application/json")
        self.Build_payload(cdp_list)
        self.operation = Ops.messageWriteAdvanced.method
        data_response  = requests.request(method=self.operation, url=self.url, data=self.payload, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        return data_response.ok

class APISimpleMessageSubscribe(APIBase):
    pass

    def Build_suffix(self, app_name, topic, callbackUrl, includeOptional):
        return Ops.simpleMessageSubscribe.suffix.format(app_name, topic, callbackUrl,includeOptional)

    def Request(self, app_name:str, topic:str, callbackUrl, includeOptional, cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.simpleMessageSubscribe.command)
        self.url += self.Build_suffix(app_name, topic, callbackUrl, includeOptional)
        
        self.Build_headers("accept", "*/*")
        self.operation = Ops.simpleMessageSubscribe.method
        data_response  = requests.request(method=self.operation, url=self.url, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        return data_response.ok

class APISetOfMessagesSubscribe(APIBase):
    pass

    def Build_suffix(self, app_name):
        return Ops.setOfMessagesSubscribe.suffix.format(app_name)

    def Build_payload(self, topic_list:list[str], callbackUrl:str, includeOptional:bool):
        pl = SetOfMessageReadReq()
        pl.callbackAPi = callbackUrl
        pl.topics = topic_list
        pl.includeOptional = includeOptional
        self.payload = pl.model_dump_json()

    def Request(self, app_name:str, topic_list:list[str], callbackUrl:str, includeOptional:bool, cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.setOfMessagesSubscribe.command)
        self.url += self.Build_suffix(app_name)
        
        self.Build_headers("Content-Type", "application/json")
        self.Build_payload(topic_list, callbackUrl, includeOptional)

        self.operation = Ops.setOfMessagesSubscribe.method
        data_response  = requests.request(method=self.operation, url=self.url, data=self.payload, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        return data_response.ok

class APIAdvancedMessagesSubscribe(APIBase):
    pass

    def Build_suffix(self, app_name):
        return Ops.advancedMessagesSubscribe.suffix.format(app_name)

    def Build_payload(self, topic_list:list[str], callbackUrl:str):
        pl = AdvancedMessageReadReq()
        pl.callbackAPi = callbackUrl
        pl.topics = topic_list
        self.payload = pl.model_dump_json()

    def Request(self, app_name:str, topic_list:list[str], callbackUrl:str, cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.advancedMessagesSubscribe.command)
        self.url += self.Build_suffix(app_name)
        
        self.Build_headers("Content-Type", "application/json")
        self.Build_payload(topic_list, callbackUrl)

        self.operation = Ops.advancedMessagesSubscribe.method
        data_response  = requests.request(method=self.operation, url=self.url, data=self.payload, headers=self.headers, timeout=cfg.api_timeout)
        data_response.raise_for_status()
        return data_response.ok

class APIDeleteAllSubscriptions(APIBase):
    pass

    def Build_suffix(self, app_name):
        return Ops.deleteAllSubscriptions.suffix.format(app_name)

    def Request(self, app_name:str, cfg: ApiConfig):
        self.Build_url(cfg.api_url, Ops.deleteAllSubscriptions.command)
        self.url += self.Build_suffix(app_name)
        
        self.Build_headers("accept", "*/*")
        self.operation = Ops.deleteAllSubscriptions.method
        data_response  = requests.request(method=self.operation, url=self.url, headers=self.headers, timeout=cfg.api_timeout)
        if data_response.status_code != HTTPStatus.NOT_FOUND:
            data_response.raise_for_status()
        return data_response.ok