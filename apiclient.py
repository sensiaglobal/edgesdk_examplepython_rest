#
# Copyright (c) 2025 Sensia Global
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
# 
# Python client interface for HCC2 SDK 2.0
#
from datetime import datetime
import os
from pydantic import BaseModel
import requests

from classes.api_classes import APIAdvancedMessagesSubscribe, APICheckProvision, APIDeleteAllSubscriptions, APIExtractConfiguration, APIHeartbeatApplication, APIInitializeApplication, APIMessageRead, APIMessageReadAdvanced, APIMessageWrite, APIMessageWriteAdvanced, APIRegisterApplication, APISetOfMessagesSubscribe, APISimpleMessageSubscribe, APIValidateProvision, MessageWriteAdvancedReq, SetDatapoint, TvqtDataPoint
from classes.enums import quality_enum
from config.apiconfig import ApiConfig, EnvVariables
from config.varsdict import VarsDict
from lib.miscfuncs import validateUrl


class APIClient(BaseModel):
    app_name: str
    connected: bool = False
    valid: bool = False
    cfg: ApiConfig = {}
    vars_dict: VarsDict = VarsDict()

    def connect(self):
        #
        # Read Environment variables
        #
        self.cfg = ApiConfig()
        env = EnvVariables()
        self.cfg.api_url = os.environ.get(env.api_url, self.cfg.api_url)
        self.cfg.api_callback_url = os.environ.get(env.api_callback_url, self.cfg.api_callback_url)
        if (self.cfg.api_url != ""):
            # check if its a vaild URL
            self.valid = validateUrl(self.cfg.api_url)    
        if (self.cfg.api_callback_url !=""):
            self.valid &= validateUrl(self.cfg.api_callback_url)    
        
        if self.valid == True:
            self.valid = self.wait_for_rest_server(self.cfg.api_test_topic)
        return self.valid
    
    def wait_for_rest_server(self, topic):
        try:
            response = self.messageRead([topic])
            if response:
                return True
        except requests.exceptions.RequestException:
            pass
        return False


    def initializeApp(self):
        message_init_app = APIInitializeApplication()
        response = message_init_app.Request(self.app_name, self.cfg)
        return response

    def registerApp(self, tarfile_path:str, is_complex_provisioned: bool):
        message_register_app = APIRegisterApplication()
        response = message_register_app.Request(self.app_name, tarfile_path, is_complex_provisioned, self.cfg)
        return response

    def heartbeatApp(self, up: bool):
        message_heartbeat_app = APIHeartbeatApplication()
        response = message_heartbeat_app.Request(self.app_name, up, self.cfg)
        return response

    def checkProvisioningStatus(self):
        message_check_provision = APICheckProvision()
        response = message_check_provision.Request(self.app_name, self.cfg)
        return response

    def validateProvision(self, valid):
        message_validate_provision = APIValidateProvision()
        response = message_validate_provision.Request(self.app_name, valid, self.cfg)
        return response

    def extractConfigFile(self, tar_file_path):
        message_extract_config = APIExtractConfiguration()
        response = message_extract_config.Request(self.app_name, tar_file_path, self.cfg)
        return response

    def messageRead(self, topic_list):
        message_read = APIMessageRead()
        response_array = message_read.Request(topic_list, self.cfg)
        return response_array
    
    def messageReadVar(self, var_list):
        topic_list = []
        for var in var_list:
            topic_list.append(self.vars_dict.get_by_var(var).topic)

        return self.messageRead(topic_list)
        
    def messageReadAdvanced(self, topic_list):
        message_read = APIMessageReadAdvanced()
        response_array = message_read.Request(topic_list, self.cfg)
        return response_array
    
    def messageReadAdvancedVar(self, var_list):
        if self.vars_dict.by_var == {}:
            raise Exception (f"vars support is not available")
        topic_list = []
        for var in var_list:
            topic_list.append(self.vars_dict.get_by_var(var).topic)
        return self.messageReadAdvanced(topic_list)

    def messageWrite(self, tvqt_datapoint_list):
        message_write = APIMessageWrite()
        response_array = message_write.Request(tvqt_datapoint_list, self.cfg)
        return response_array

    def messageWriteVar(self, var_list):
        tvqt_datapoint_list = []
        for var in var_list:
            topic = self.vars_dict.get_by_var(var.name).topic
            tvqt_datapoint = TvqtDataPoint(topic=topic, value = var.value, quality = quality_enum.OK, timeStamp = datetime.now())
            tvqt_datapoint_list.append(tvqt_datapoint)
        return self.messageWrite(tvqt_datapoint_list)

    def messageWriteAdvanced(self, complex_datapoint_list):
        message_write = APIMessageWriteAdvanced()
        response_array = message_write.Request(complex_datapoint_list, self.cfg)
        return response_array
    
    def messageWriteAdvancedVar(self, var_list):
        if self.vars_dict.by_var == {}:
            raise Exception (f"vars support is not available")
        complex_datapoint_list = []
        for var in var_list:
            topic = self.vars_dict.get_by_var(var.name).topic
            if topic is not None: 
                complex_datapoint = MessageWriteAdvancedReq(topic=topic, msgSource=self.cfg.api_msg_source,
                    datapoints=[
                        SetDatapoint(
                            dataPointName="", 
                            quality = quality_enum.OK, 
                            timeStamps=[datetime.now()],
                            values=[var.value])])

                complex_datapoint_list.append(complex_datapoint)
            else:
                raise Exception (f"var: {var.name} is invalid")            
        return self.messageWriteAdvanced(complex_datapoint_list)

    def deleteAllSubscriptions(self, app_name):
        delete_subscriptions = APIDeleteAllSubscriptions()
        response_array =delete_subscriptions.Request(app_name, self.cfg)
        return response_array

    def simpleSubscribe(self, app_name, topic, callback_url, includeOptional):
        simple_subscribe = APISimpleMessageSubscribe()
        response_array = simple_subscribe.Request(app_name, topic, callback_url, includeOptional, self.cfg)
        return response_array
    
    def setOfMessagesSubscribe(self, app_name, topic_list, callback_url, includeOptional):
        set_of_messages_subscribe = APISetOfMessagesSubscribe()
        response_array = set_of_messages_subscribe.Request(app_name, topic_list, callback_url, includeOptional, self.cfg)
        return response_array

    def advancedMessagesSubscribe(self, app_name, topic_list, callback_url):
        advanced_messages_subscribe = APIAdvancedMessagesSubscribe()
        response_array = advanced_messages_subscribe.Request(app_name, topic_list, callback_url, self.cfg)
        return response_array

    