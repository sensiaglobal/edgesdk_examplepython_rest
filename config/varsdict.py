#
# Copyright (c) 2025 Sensia Global
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
import json
from pydantic import BaseModel

class VarDecoder(BaseModel):
    def var_decoder(self, dct):
        return Var(var=dct['var'], topic=dct['topic'], type=dct['type'], size=dct['size'], writable=dct['writable'])

class Var(BaseModel):
    var:str = ""
    topic:str = ""
    type:str = ""
    size:int = 0
    writable: bool = False

    def from_json(self, json_string):
        return json.loads(json_string, object_hook=VarDecoder().var_decoder)

class VarsDict(BaseModel):
    by_topic:dict = {}
    by_var:dict = {}

    def set (self, topic, var, data):
        self.by_topic[topic] = data
        self.by_var[var] = data

    def get_by_topic(self, topic):
        return self.by_topic.get(topic)
    
    def get_by_var(self, var):
        return self.by_var.get(var)

    def load(self, array):
        for var in array:
            self.set(var.topic, var.var, var)
        return self
    