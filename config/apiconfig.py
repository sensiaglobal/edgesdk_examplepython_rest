#
# Copyright (c) 2025 Sensia Global
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# Python client interface for HCC2 SDK 2.0
#
from typing import ClassVar
from pydantic import BaseModel

class EnvVariables(BaseModel):
     api_url: str = "HCC2_SDK2_API_URL"
     api_callback_url: str = "SDK2_CALLBACK_URL"

class ApiConfig (BaseModel):
    api_url: str = ""
    api_callback_url: str = ""
    api_version: str = "0.0.0"
    api_suffix: str = "api/v1"
    api_timeout: int = 10
    datetime_query_format: str = "%Y-%m-%dT%H:%M:%S.000Z"
    api_msg_source:str = "REST"
    api_test_topic: str = "liveValue.state.this.core.0.up."

class Operation(BaseModel):
      method: str
      command: str
      suffix: str

class Ops (BaseModel):
    messageInitializeApplication: ClassVar[Operation] = Operation(method="PUT", command="/app-creator", suffix="/{0}/defaults")
    messageRegisterApplication:  ClassVar[Operation] = Operation(method="POST", command="/app-registration", suffix="/{0}?isComplexProvisioned={1}")
    messageHeartbeatApplication: ClassVar[Operation] = Operation(method="PUT", command="/app-provision", suffix="/{0}")
    messageExtractConfiguration: ClassVar[Operation] = Operation(method="GET", command="/app-provision", suffix="/{0}/targz")
    messageCheckProvision: ClassVar[Operation] = Operation(method="GET", command="/app-provision", suffix="/{0}")
    messageValidateProvision: ClassVar[Operation] = Operation(method="POST", command="/app-provision", suffix="/{0}")
    messageCreateGeneralDatapoints: ClassVar[Operation] = Operation(method="PUT", command="/app-creator", suffix="/{0}/datapoint/general")
    messageRead: ClassVar[Operation] = Operation(method="POST", command="/message/read", suffix="")
    messageReadAdvanced: ClassVar[Operation] = Operation(method="POST", command="/message/read-advanced", suffix="")
    messageWrite: ClassVar[Operation] = Operation(method="POST", command="/message/write", suffix="")
    messageWriteAdvanced: ClassVar[Operation] = Operation(method="POST", command="/message/write-advanced", suffix="")
    deleteAllSubscriptions: ClassVar[Operation] = Operation(method="DELETE", command="/message/subscription", suffix="/{0}")
    simpleMessageSubscribe: ClassVar[Operation] = Operation(method="PUT", command="/message/subscription", suffix="/{0}/{1}?callbackapi={2}&includeOptional={3}")
    setOfMessagesSubscribe: ClassVar[Operation] = Operation(method="POST", command="/message/subscription", suffix="/{0}")
    advancedMessagesSubscribe: ClassVar[Operation] = Operation(method="POST", command="/message/subscription-advanced", suffix="/{0}")