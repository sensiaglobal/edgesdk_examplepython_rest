#
# Copyright (c) 2025 Sensia Global
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
from pydantic import BaseModel

class App(BaseModel):
    name:str = "courseApp"
    tarfile_path:str = "data/courseApp.tar.gz"
    var_config_path: str = "config/vars.json"
    complex_provisioned: bool = False
    webhook_enabled:bool = False
    vars_enabled:bool = False

class Operation(BaseModel):
        command:str
        operation:str

class WhApp(BaseModel):
    host:str = "0.0.0.0"
    protocol:str = "http"
    suffix:str = "/webhook/v1/"
    group_tag: str = "Subscriptions"
    port:int = 8100
    test:Operation = Operation(command="test", operation="GET")
    simple_message:Operation = Operation(command="simple_message", operation="POST")
    set_of_messages:Operation = Operation(command="set_of_messages", operation="POST")
    advanced_messages:Operation = Operation(command="advanced_messages", operation="POST")

class Misc(BaseModel):
    retry_period:int = 1
    hearbeat_initial_state: bool = False
    heartbeat_period: int = 10
    app_loop_period: int = 1
    provision_time: int = 10
    error_retries: int = 10

class Log (BaseModel):
    log_to_file: bool = False
    log_file:str = "logs/app.log"
    level:str = "INFO"
    api_level:str = "ERROR"
    format:str = "[0][%(asctime)s.%(msecs)03dZ][%(name)s][%(levelname)s]%(message)s"
    date_format:str = "%Y-%m-%dT%H:%M:%S"

class AppConfig (BaseModel):
    app: App = App()
    wh: WhApp = WhApp()
    misc: Misc = Misc()
    log: Log = Log()
