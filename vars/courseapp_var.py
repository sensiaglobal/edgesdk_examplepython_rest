#
# Copyright (c) 2025 Sensia Global
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# Python client interface for HCC2 SDK 2.0
# Sample app
#
from datetime import datetime
import logging
import time
import queue
from apiclient import APIClient
from classes.api_classes import MessageWriteReqVar
from classes.webhook import WebHook
from config.appconfig import AppConfig
from classes.heartbeat import HeartBeat
from config.varsdict import Var
from lib.miscfuncs import text_to_log_level
#
# Get configuration
#
appcfg = AppConfig()
#
# setup logger
#
logging.basicConfig( level=appcfg.log.level,
    format=appcfg.log.format,
    datefmt=appcfg.log.date_format)
logger = logging.getLogger(appcfg.app.name)
logger.setLevel (text_to_log_level(appcfg.log.level))
if appcfg.log.log_to_file == True:
    fh = logging.FileHandler(appcfg.log.log_file, mode='w')
    fh.setLevel(logging.getLevelName(appcfg.log.level))
    fmt = logging.Formatter(appcfg.log.format)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    logging.getLogger().propagate = False

logging.addLevelName(logging.CRITICAL, "critical")
logging.addLevelName(logging.ERROR, "error")
logging.addLevelName(logging.WARNING, "warning")
logging.addLevelName(logging.INFO, "info")
logging.addLevelName(logging.DEBUG, "debug")

###############################################################################################
# 
# 1. Connect with API
#
hbq = queue.Queue()

reload_required = False

client = APIClient(app_name=appcfg.app.name)

###############################################################################################
# 
# Get vars configuration data
#
if appcfg.app.vars_enabled == True:
    try:
        with open(appcfg.app.var_config_path) as json_file:
            v = Var().from_json(json_file.read())
        client.vars_dict.load(v)
    except Exception as e:
        logger.error(f"Error trying to read variable configuration file. Error: {e}. PROCESS ABORTED.")
        exit(-1)

###############################################################################################
#
# initialize webhook (optional)
# 
if appcfg.app.webhook_enabled == True:
    whq = queue.Queue()
    wh = WebHook(logger=logger, queue=whq, config=appcfg)
    #
    # Start the webhook manager as an independent thread as well
    #
    while True:
        try:
            wh.start()
            logger.debug(f"Web hook thread has been fired successfully. ")
            break
        except Exception as e:
            logger.error(f"webhook manager - Error trying to start webhook thread for  \"{client.app_name}\". Error: {e}. Retrying.")
            time.sleep(appcfg.misc.retry_period)
            continue

############################################################################################################
#
# OUTER LOOP
#
while True:
    status = client.connect()
    logger.debug(f"Connecting with API at URL: {client.cfg.api_url}")
    
    if status == False:
        logger.error(f"Connect - Error trying to connect to API at URL: {client.cfg.api_url}.  Retrying.")
        time.sleep(appcfg.misc.retry_period)
        continue 
    logger.debug(f"Connect - Application {appcfg.app.name} is connected with API")
    #
    # Set Application Heartbeat (required by Unity)
    #
    hb = HeartBeat(client, hbq, appcfg.misc.hearbeat_initial_state, appcfg.misc.heartbeat_period)

    ###############################################################################################
    #
    # 2. register App using existing stored tarball (TEST)
    #
    try:
        response = client.registerApp(tarfile_path=appcfg.app.tarfile_path, is_complex_provisioned=appcfg.app.complex_provisioned)
        logger.debug(f"Application {client.app_name} correcty registered to API using tar.gz file: {appcfg.app.tarfile_path}")
    except Exception as e:
        logger.error(f"registerApp - Error trying to register application \"{client.app_name}\". Error: {e}. Retrying.")
        time.sleep(appcfg.misc.retry_period)
        continue

    ###############################################################################################
    #
    # 3. Start the heartbeat as an independent thread
    #
    try:
        hb.start()
        logger.debug(f"Heartbeat thread has been fired successfully. ")
    except Exception as e:
        logger.error(f"heartbeat - Error trying to start heartbeat thread for  \"{client.app_name}\". Error: {e}.  Retrying.")
        time.sleep(appcfg.misc.retry_period)
        continue
    #
    logger.debug (f"Wait {appcfg.misc.provision_time} for configuration to settle down....")
    time.sleep(appcfg.misc.provision_time)
    ###############################################################################################
    #
    # 5. Check if a new deployment was done just after app registering
    #
    fail = False
    while not fail:
        try:
            response = client.checkProvisioningStatus()
            logger.debug (f"checkProvisioningStatus responded ok")
        except Exception as e:
            logger.error(f"checkProvisioningStatus - Error trying to check provision application \"{client.app_name}\". Error: {e}.  Retrying.")
            fail = True
            break

        if response.hasNewConfig == True:
            logger.debug(f"checkProvisioningStatus -> New configuration found! ")
            break
        time.sleep(appcfg.misc.retry_period)
    
    if fail == True:
        time.sleep(appcfg.misc.retry_period)
        continue

    ###############################################################################################
    #
    # 6. Set provisioning valid true
    #
    try:
        response = client.validateProvision(valid=True)
        logger.debug (f"validateProvision responded ok")
    except Exception as e:
        logger.error(f"validateProvision -Error trying to validate provision \"{client.app_name}\". Error: {e}.  Retrying.")
        time.sleep(appcfg.misc.retry_period)
        continue
    ###############################################################################################
    #
    # 7. Change heartbeat to isUp=true
    #
    hb.change_state(True)
    #
    # End of road - all configuration good!
    break

###############################################################################################
#
# 8. INNER LOOP - Here comes the app business logic
#
run_counter = 1

while True:
    
    #################################################################################################
    #
    # Read Configuration Parameters:
    #
    try:
        value_array = client.messageReadVar(
            [
                "configRunningPeriod"
            ]
        )
        for val in value_array:
            logger.debug(f"topic: {val.topic}, value: {val.value}, type: {type(val.value)}, quality: {val.quality}, timeStamp: {val.timeStamp}")
    except Exception as e:
        logger.error(f"messageRead Error trying to read vars:  \"{client.app_name}\". Error: {e}.  Try Again.")
        time.sleep(appcfg.misc.retry_period)
        continue
    period = int(value_array[0].value)
    if period < 1: 
        period = 1
    if period > 100:
        period = 100
    #
    # Read Configuration parameters using Vars
    #
    try:
        value_array = client.messageReadVar(
            [
                "ioTemp"
            ]
        )
        for val in value_array:
            logger.debug(f"topic: {val.topic}, value: {val.value}, type: {type(val.value)}, quality: {val.quality}, timeStamp: {val.timeStamp}")
    except Exception as e:
        logger.error(f"messageRead Error trying to read vars:  \"{client.app_name}\". Error: {e}.  Try Again.")
        time.sleep(appcfg.misc.retry_period)
        continue
    #########################################################################################################################3
    #
    # Read Configuration parameters (using Read Advanced with Vars)
    #
    try:
        response_array = client.messageReadAdvancedVar(
            [
                "cpuUsage"
            ]
        )
        for resp in response_array:
            for dp in resp.datapoints:
                logger.debug(f"topic: {resp.topic}, quality: {dp.quality}")
                for i in range(len(dp.values)):
                    if dp.dataPointName == "total.":
                        cpu_usage = dp.values[i]
                        break

                logger.debug(f"item: {i+1}, datapoint_name: {dp.dataPointName},  value: {dp.values[i]}, type: {type(dp.values[i])} timeStamp: {dp.timeStamps[i]}")
    
    except Exception as e:
        logger.error(f"messageRead Error trying to read tags:  \"{client.app_name}\". Error: {e}. Try Again.")
        time.sleep(appcfg.misc.retry_period)
        continue
    #
    #
    if run_counter == 1:
        cpu_usage_max = cpu_usage
        cpu_usage_min = cpu_usage
    else:
        if cpu_usage > cpu_usage_max:
            cpu_usage_max = cpu_usage
        elif cpu_usage < cpu_usage_min:
            cpu_usage_min = cpu_usage

    tvqt_datapoint_list = [
        MessageWriteReqVar(name ="runCounter", value = run_counter),
        MessageWriteReqVar(name ="lastRunTime", value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        MessageWriteReqVar(name ="cpuUsageCurrent", value = cpu_usage),
        MessageWriteReqVar(name ="cpuUsageMax", value = cpu_usage_max),
        MessageWriteReqVar(name ="cpuUsageMin", value = cpu_usage_min),
    ]

    try:
        status = client.messageWriteVar(tvqt_datapoint_list)
        logger.debug (f"messageWrite - Writing: {tvqt_datapoint_list}. status: {status}")
    except Exception as e:
        logger.error(f"messageWrite Error trying to write tags:  \"{client.app_name}\". Error: {e}. Try again.")
        time.sleep(appcfg.misc.retry_period)
        continue 

    #time.sleep(appcfg.misc.app_loop_period)
    run_counter += 1
    time.sleep(period)

thread.join()

