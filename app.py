#
# Copyright (c) 2025 Sensia Global
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# Python client interface sample for HCC2 Rest API Server
# Sample app
#
from datetime import datetime
import logging
import time
import queue
from apiclient import APIClient
from classes.api_classes import TvqtDataPoint
from classes.enums import quality_enum
from classes.log_control import LogControl
from classes.webhook import WebHook
from config.appconfig import AppConfig
from classes.heartbeat import HeartBeat
from config.varsdict import Var
from lib.miscfuncs import text_to_log_level
from lib.webhookfuncs import dequeue
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
reload_required = False

client = APIClient(app_name=appcfg.app.name)
###############################################################################################
hbq = queue.Queue()
#
# Set Application Heartbeat (required by Unity)
#
hb = HeartBeat(logger, client, hbq, appcfg.misc.hearbeat_initial_state, appcfg.misc.heartbeat_period)
log_control = LogControl(logger=logger, retry_period=appcfg.misc.retry_period, max_retries=appcfg.misc.error_retries, heartbeat_obj=hb, client_name=client.app_name)

################################################################################################
# 
# Get vars configuration data (optional)
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

############################################################################################################
#
# OUTER LOOP
#
log_control.reset_retries()

while True:
    log_control.check_retries()
    status = client.connect()
    logger.info(f"Connecting with API at URL: {client.cfg.api_url}")
    if status == False:
        logger.error(f"Connect - Error trying to connect to API at URL: {client.cfg.api_url}.  Retrying.")
        time.sleep(appcfg.misc.retry_period)
        continue
            
    logger.debug(f"Connect - Application {appcfg.app.name} is connected with API")
    
    ###############################################################################################
    #
    # 2. register App using existing stored tarball (TEST)
    #
    try:
        response = client.registerApp(tarfile_path=appcfg.app.tarfile_path, is_complex_provisioned=appcfg.app.complex_provisioned)
        logger.info(f"Application {client.app_name} correcty registered to API using tar.gz file: {appcfg.app.tarfile_path}")
    except Exception as e:
        logger.error(f"registerApp - Error trying to register application. Config file: \"{appcfg.app.tarfile_path}\". Error: {e}. Retrying.")      
        time.sleep(appcfg.misc.retry_period)
        continue

    ###############################################################################################
    #
    # 3. Start the heartbeat as an independent thread
    #
    try:
        hb.start()
        logger.info(f"Heartbeat thread has been fired successfully. ")

    except Exception as e:
        logger.error(f"heartbeat - Error trying to start heartbeat thread. Error: {e}.  Retrying.")
        time.sleep(appcfg.misc.retry_period)
        continue
    #
    logger.debug (f"Wait {appcfg.misc.provision_time} for configuration to settle down....")
    time.sleep(appcfg.misc.provision_time)

    ###############################################################################################
    #
    # 5. Check if a new deployment was done just after app registering
    #
    while True:
        try:
            response = client.checkProvisioningStatus()
            logger.debug (f"checkProvisioningStatus responded ok")
        except Exception as e:
            logger.error(f"checkProvisioningStatus - Error trying to check provision status. Error: {e}.  Retrying.")
            time.sleep(appcfg.misc.retry_period)
            continue

        if response.hasNewConfig == True:
            logger.info(f"checkProvisioningStatus -> New configuration found! ")
            break
        time.sleep(appcfg.misc.retry_period)

    ###############################################################################################
    #
    # 6. Set provisioning valid true
    #
    try:
        response = client.validateProvision(valid=True)
        logger.debug (f"validateProvision responded ok")
    except Exception as e:
        logger.error(f"validateProvision -Error trying to validate provision. Error: {e}.  Retrying.")
        time.sleep(appcfg.misc.retry_period)
        continue
    ###############################################################################################
    #
    # 7. Change heartbeat to isUp=true
    #
    hb.change_state(True)
    #
    #  Examples using webhooks:
    #
    if appcfg.app.webhook_enabled == True:
        #
        # initialize subscribed topics
        #
        subscribed = dict()
        #
        # Delete all subscriptions 
        #
        try:
            status = client.deleteAllSubscriptions(client.app_name)
            logger.debug (f"DeleteAllSubscriptions - completed succesfully.")
            if status == False:
                logger.warning(f"DeleteAllSubscriptions - no susbcriptions were found.")    
        except Exception as e:
            logger.error(f"DeleteAllSubscriptions - Error trying to subscribe. Check parameters and configuration. Error: {e}. Try again.")
            time.sleep(appcfg.misc.retry_period)
            continue
        #
        # Subscribe to one topic using SimpleSubscribe
        #
        topic1 = "liveValue.state.this.io.0.general.upTime."
        subscribed[topic1] = {}
        callback_url = client.cfg.api_callback_url + "/" + appcfg.wh.simple_message.command

        try:
            status = client.simpleSubscribe(client.app_name, topic1, callback_url, True)
            logger.debug (f"SimpleSubscribe for topic {topic1} on url {callback_url} completed succesfully.")
        except Exception as e:
            logger.error(f"SimpleSubscribe - Error trying to subscribe. Check parameters and configuration. Error: {e}. Try again.")
            time.sleep(appcfg.misc.retry_period)
            continue
        #
        # Subscribe to other topics using setOfMessagesSubscribe
        #
        topic_list = ["liveValue.diagnostics.this.io.0.temperature.cpu.",
                    "liveValue.diagnostics.this.io.0.rail.voltage.v1p2."
                    ]

        subscribed[topic_list[0]] = {}
        subscribed[topic_list[1]] = {}

        callback_url = client.cfg.api_callback_url + "/" + appcfg.wh.set_of_messages.command
        try:
            status = client.setOfMessagesSubscribe(client.app_name, topic_list, callback_url, True)
            logger.debug (f"SetOfMessagesSubscribe for topic List {topic_list} on url {callback_url} completed succesfully.")
        except Exception as e:
            logger.error(f"SetOfMessagesSubscribe - Error trying to subscribe. Check parameters and configuration. Error: {e}. Try again.")
            time.sleep(appcfg.misc.retry_period)
            continue
        #
        # Subscribe to other topics using advanced Message
        #
        topic_list = ["liveValue.diagnostics.this.core.0.diskUsage|.",
                    "liveValue.diagnostics.this.io.0.rail.voltage.v3p3."
                    ]

        subscribed[topic_list[0]] = {}
        subscribed[topic_list[1]] = {}
        
        callback_url = client.cfg.api_callback_url + "/" + appcfg.wh.advanced_messages.command
        try:
            status = client.advancedMessagesSubscribe(client.app_name, topic_list, callback_url)
            logger.debug (f"AdvancedMessagesSubscribe for topic List {topic_list} on url {callback_url} completed succesfully.")
        except Exception as e:
            logger.error(f"AdvancedMessagesSubscribe - Error trying to subscribe. Check parameters and configuration. Error: {e}. Try again.")
            time.sleep(appcfg.misc.retry_period)
            continue
        ###############################################################################################
        # 
        # Start the webhook thread
        #
        while True:
            log_control.check_retries()
            try:
                wh.start()
                logger.debug(f"Web hook thread has been fired successfully. ")
                break
            except Exception as e:
                logger.error(f"webhook manager - Error trying to start webhook thread for  \"{client.app_name}\". Error: {e}. Retrying.")
                time.sleep(appcfg.misc.retry_period)
                continue

    ###############################################################################################
    #
    # Store datetime of 1st run
    #
    tvqt_datapoint_list = [
            TvqtDataPoint(topic ="liveValue.production.this.courseApp.0.firstruntime.", 
            value = datetime.now().strftime("%Y-%m-%d %H:%M:%S"), quality = quality_enum.OK, timeStamp = datetime.now()),
        ]

    try:
        status = client.messageWrite(tvqt_datapoint_list)
        logger.debug (f"messageWrite - Writing: {tvqt_datapoint_list}. status: {status}")
    except Exception as e:
        logger.error(f"messageWrite - Error trying to write tags. Check topic spelling. Error: {e}. Try again.")
        time.sleep(appcfg.misc.retry_period)
        continue
    #
    # End of road - all configuration good!
    break
###############################################################################################
# 
# 8. INNER LOOP - Here comes the app business logic
#
run_counter = 1
cpu_usage = 0
memory_usage = 0
temperature = 0

log_control.reset_retries()

while True:
    
    #################################################################################################
    #
    # Read Configuration Parameters:
    #
    try:
        value_array = client.messageRead(
            [
                "liveValue.postvalidConfig.this.courseApp.0.configrunningperiod.",
                "liveValue.postvalidConfig.this.courseApp.0.maxminrestartperiod."
            ]
        )
        for val in value_array:
            logger.debug(f"topic: {val.topic}, value: {val.value}, type: {type(val.value)}, quality: {val.quality}, timeStamp: {val.timeStamp}")
    except Exception as e:
        logger.error(f"messageRead - Error trying to read topics. Check topics spelling. Error: {e}.  Try Again.")
        time.sleep(appcfg.misc.retry_period)
        continue

    period = int(value_array[0].value)
    if period < 1: 
        period = 1
    if period > 60:
        period = 60

    restart_period = int(value_array[1].value)
    if period < 1: 
        period = 1
    if period > 60:
        period = 60
    #
    # Read Configuration parameters using Vars
    #
    try:
        value_array = client.messageRead(
            [
                "liveValue.diagnostics.this.io.0.temperature.cpu."
            ]
        )
        for val in value_array:
            logger.debug(f"topic: {val.topic}, value: {val.value}, type: {type(val.value)}, quality: {val.quality}, timeStamp: {val.timeStamp}")
        temperature = value_array[0].value

    except Exception as e:
        logger.error(f"messageRead - Error trying to read topics. Check topic spelling. Error: {e}.  Try Again.")
        time.sleep(appcfg.misc.retry_period)
        continue
    #########################################################################################################################3
    #
    # Read Configuration parameters (using Read Advanced with Vars)
    #
    try:
        response_array = client.messageReadAdvanced(
            [
                "liveValue.diagnostics.this.core.0.cpuUsage|.",
                "liveValue.diagnostics.this.core.0.memoryUsage|."
            ]
        )
        if len(response_array) == 0:
            raise Exception ("One or more topics do not exist. Check topic string.")
        for resp in response_array:
            for dp in resp.datapoints:
                logger.debug(f"topic: {resp.topic}, quality: {dp.quality}")
                for i in range(len(dp.values)):
                    if dp.dataPointName == "total.":
                        cpu_usage = dp.values[i]
                        break
                    elif dp.dataPointName == "memoryUsed.":
                        memory_usage = dp.values[i]
                        break

                logger.debug(f"item: {i+1}, datapoint_name: {dp.dataPointName},  value: {dp.values[i]}, type: {type(dp.values[i])} timeStamp: {dp.timeStamps[i]}")
    
    except Exception as e:
        logger.error(f"messageReadAdvanced - Error trying to read tags. Check topic spelling. Error: {e}. Try Again.")
        time.sleep(appcfg.misc.retry_period)
        continue
    #
    #
    ts = datetime.now() 
    if ts.minute % restart_period == 0 and ts.second == 0:
        run_counter = 1

    if run_counter == 1:
        cpu_usage_max = cpu_usage
        cpu_usage_min = cpu_usage
        memory_usage_max = memory_usage
        memory_usage_min = memory_usage
    else:
        if cpu_usage > cpu_usage_max:
            cpu_usage_max = cpu_usage
        elif cpu_usage < cpu_usage_min:
            cpu_usage_min = cpu_usage
        if memory_usage > memory_usage_max:
            memory_usage_max = memory_usage
        elif memory_usage < memory_usage_min:
            memory_usage_min = memory_usage
        

    tvqt_datapoint_list = [
        TvqtDataPoint(topic ="liveValue.production.this.courseApp.0.runcounter.", 
        value = run_counter, quality = quality_enum.OK, timeStamp = datetime.now()),
        TvqtDataPoint(topic ="liveValue.production.this.courseApp.0.lastruntime.", 
        value = datetime.now().strftime("%Y-%m-%d %H:%M:%S"), quality = quality_enum.OK, timeStamp = datetime.now()),
        TvqtDataPoint(topic ="liveValue.production.this.courseApp.0.cpuusagecurrent.", 
        value = cpu_usage, quality = quality_enum.OK, timeStamp = datetime.now()),
        TvqtDataPoint(topic ="liveValue.production.this.courseApp.0.cpuusagemax.", 
        value = cpu_usage_max, quality = quality_enum.OK, timeStamp = datetime.now()),
        TvqtDataPoint(topic ="liveValue.production.this.courseApp.0.cpuusagemin.", 
        value = cpu_usage_min, quality = quality_enum.OK, timeStamp = datetime.now()),
        TvqtDataPoint(topic ="liveValue.production.this.courseApp.0.memoryusagecurrent.", 
        value = memory_usage, quality = quality_enum.OK, timeStamp = datetime.now()),
        TvqtDataPoint(topic ="liveValue.production.this.courseApp.0.memoryusagemax.", 
        value = memory_usage_max, quality = quality_enum.OK, timeStamp = datetime.now()),
        TvqtDataPoint(topic ="liveValue.production.this.courseApp.0.memoryusagemin.", 
        value = memory_usage_min, quality = quality_enum.OK, timeStamp = datetime.now()),
        TvqtDataPoint(topic ="liveValue.production.this.courseApp.0.temperature.", 
        value = temperature, quality = quality_enum.OK, timeStamp = datetime.now())
    ]

    try:
        status = client.messageWrite(tvqt_datapoint_list)
        logger.debug (f"messageWrite - Writing: {tvqt_datapoint_list}. status: {status}")
    except Exception as e:
        logger.error(f"messageWrite - Error trying to write tags. Check topic spelling. Error: {e}. Try again.")
        time.sleep(appcfg.misc.retry_period)
        continue
    #
    # if wbhook enabled:
    #
    if appcfg.app.webhook_enabled == True:
        #
        # Dequeue async messages coming from webhook (if enabled)
        #
        try:
            payloads = dequeue(whq)
        except Exception as e:
            logger.error(f"Webhook message dequeue - Error trying to dequeue messages from webhook. Error: {e}.")
        if len(payloads) > 0:
            for pl in payloads:
                if pl.topic in subscribed:
                        subscribed[pl.topic]=pl
                else:
                    logger.warning (f"Topic {pl.topic} is not subscribed by this application. Check configuration.")

    run_counter += 1
    time.sleep(period)
thread.join()

