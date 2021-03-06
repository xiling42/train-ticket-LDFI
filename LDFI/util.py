# -*- coding: utf-8 -*-
"""
This file contains utility functinos for LDFI. Including fault injection and recovery, Jaeger traces extraction and retrival.
Created on Sat Nov 21 00:38:07 2020

@author: Xiling Zhang, Qingyi Lu
"""
import os
import time
import subprocess, json
import logging
import platform
from pathlib import Path
from datetime import datetime, timedelta
import yaml

# requests = ['type_admin_get_orders', 'type_simple_search', 'type_admin_get_route', 
#             'type_admin_get_travel', 'type_admin_login',
#             'type_cheapest_search', 'type_food_service', 'type_preserve',
#             'type_user_login']
requests = ['type_admin_get_route', 'type_food_service', 'type_simple_search', 'type_admin_get_orders', 'type_admin_get_travel', 'type_admin_login',
                'type_cheapest_search',  'type_preserve', 'type_user_login']
#requests = ['type_admin_get_orders']

# ts-security-service.default.svc.cluster.local:11188/*
jmeter_path = Path('./jmeter/apache-jmeter-5.3/bin')
request_to_entry_service = {'type_admin_get_orders' : 'ts-admin-order-service',
                            'type_admin_get_route':'ts-admin-route-service',
                            'type_admin_get_travel': 'ts-admin-travel-service',
                            'type_admin_login':'ts-admin-user-service',
                            'type_cheapest_search':'ts-travel-plan-service',
                            'type_food_service': 'ts-food-map-service',
                            'type_preserve' : 'ts-preserve-service',
                            'type_user_login': 'ts-user-service',
                            'type_simple_search': 'ts-ticketinfo-service'}

request_to_operation = {'type_admin_get_orders' : 'getAllOrders',
                            'type_admin_get_route':'getAllRoutes',
                            'type_admin_get_travel': 'getAllTravels',
                            'type_admin_login':'getAllTravels',
                            'type_cheapest_search':'getByCheapest',
                            'type_food_service': 'getAllFood',
                            'type_preserve' : 'preserve',
                            'type_user_login': 'preserve'}
jmeter_folder = Path('./jmeter')
request_folder = os.path.join(jmeter_folder, 'jmeter_code')
request_log_folder = os.path.join(request_folder, 'logs')

def inject_and_get_trace(list_service, fault, request_type):
    # for given fault and request type, inject failures. 
    # After injection and getting traces, this function will also remove injected failures. 
    
    injected_files = []
    
    for service in list_service:
        # generate yaml
        service_name = service.split('.')[0]
        _write_yaml(service_name, fault)
        time.sleep(2)
        file_name = service_name + '-' + fault + '.yml'
        command = 'kubectl apply -f {}'.format(file_name)
        injected_files.append(file_name)
        print('Inject: ', command)
        proc = subprocess.Popen(command, shell=True,  stdout=subprocess.PIPE)
        json_data, error = proc.communicate()
        
    try:

        request_result = _get_request_by_type(request_type, False)

    except:
        print('keep going and look at log later')
        return []
    
    print('~~~~Inject Filies: ', injected_files)
    for file in injected_files:
        time.sleep(1)
        command = 'kubectl delete -f {}'.format(file)
        print('Remove injecting: ', command)
        proc = subprocess.Popen(command, shell=True,  stdout=subprocess.PIPE)
        
    return request_result
  
def get_request_type_traces(targeted_requests = requests):
    # for given requests, run them and get all traces in dictionary. Requests are default to be all request types.
    
    traces = dict()
    
    for request in targeted_requests:
        if request not in requests:
            print('request not exist')
            continue
        #request_path = os.path.join(jmx_path, request+'.jmx')
        services = _get_request_by_type(request, True)
        traces[request] = services
        # services.sort(key = lambda x: -len(x))
        # if not services:
        #     traces[request] = []
        # else:
        #     services = list(set(services[0]))
        #     traces[request] = services
    return traces

def inject_and_get_error_requests(list_service, fault, remain_requests = requests):
    # for given fault and request type, inject failures. 
    # After injection and getting traces, this function will also remove injected failures. 
    
    injected_files = []
    result_errored_services = []
    for service in list_service:
        # generate yaml
        service_name = service.split('.')[0]
        _write_yaml(service_name, fault)
        time.sleep(2)
        file_name = service_name + '-' + fault + '.yml'
        command = 'kubectl apply -f {}'.format(file_name)
        injected_files.append(file_name)
        print('Inject: ', command)
        proc = subprocess.Popen(command, shell=True,  stdout=subprocess.PIPE)
        json_data, error = proc.communicate()
        
    try:
       
        for request in remain_requests:
            services = _get_request_by_type(request, False)
            if not services:
                result_errored_services.append(request)
    
    except:
        print('keep going and look at log later')
        return []
    
    print('~~~~Inject Filies: ', injected_files)
    for file in injected_files:
        time.sleep(1)
        command = 'kubectl delete -f {}'.format(file)
        print('Remove injecting: ', command)
        proc = subprocess.Popen(command, shell=True,  stdout=subprocess.PIPE)
        
    return result_errored_services

def inject_and_get_error_requests2( list_service, remain_requests = requests):
    # for given fault and request type, inject failures. 
    # After injection and getting traces, this function will also remove injected failures. 
    
    injected_files = []
    result_errored_services = []
    for service, fault in list_service:
        # generate yaml
        service_name = service.split('.')[0]
        _write_yaml(service_name, fault)
        time.sleep(2)
        file_name = service_name + '-' + fault + '.yml'
        command = 'kubectl apply -f {}'.format(file_name)
        injected_files.append(file_name)
        print('Inject: ', command)
        proc = subprocess.Popen(command, shell=True,  stdout=subprocess.PIPE)
        json_data, error = proc.communicate()
        
    try:
       
        for request in remain_requests:
            services = _get_request_by_type(request, False)
            if not services:
                result_errored_services.append(request)
    
    except:
        print('keep going and look at log later')
        return []
    
    print('~~~~Inject Filies: ', injected_files)
    for file in injected_files:
        time.sleep(1)
        command = 'kubectl delete -f {}'.format(file)
        print('Remove injecting: ', command)
        proc = subprocess.Popen(command, shell=True,  stdout=subprocess.PIPE)
        
    return result_errored_services

def _write_yaml(service_name, fault_type):
    # create a yaml file for given service and fault type. 
    print('debug: ', service_name)
    if fault_type == 'delay':
        template = 'template_delay.yml'
    elif fault_type == 'abort':
        template = 'template_abort.yml'
    else:
        print('error in fault type. Please check!!!!')
        return
    
    with open(template) as f:
        content = yaml.load(f, Loader = yaml.FullLoader)
        
        # output: <type 'dict'>
        # print(type(content))
        # print(content)
        content['metadata']['name'] = service_name
        content['spec']['hosts'] = [service_name]
        
        for each in content['spec']['http']:
            for route in each['route']:
                route['destination']['host'] = service_name
           
    with open(service_name + '-' + fault_type + '.yml', 'w') as nf:
        yaml.dump(content, nf)
        
def _get_result_from_log(file_path):
    # get result for file
    success_index = 7
    success = True
    with open(file_path, "r") as file:
        lines = file.readlines() 
        for line in lines[1:]:
            contents = line.split(',')
            success = success and contents[success_index] == 'true'
    if os.path.exists(file_path) and success:
        os.remove(file_path) # if there is no error, remove log

    return success

def _get_request_by_type(request_type, firt_run):
    # for given type, run request and get traces. 
    # if first_run, there should be no error. Throw exception and terminate if there is any. This suggest Train Ticket works unexpected.
    # the jmeter executable file is jmeter.sh for linux. If trying to use this under windows, please change it to jmeter.bat
    request_file = os.path.join(request_folder, request_type +'.jmx')
    request_log = os.path.join(request_log_folder, request_type +'.log')
    if platform.system() == 'Linux':
        jmeter_exec = os.path.join(jmeter_path, 'jmeter.sh')
        jmeter_exec = './' + jmeter_exec
    else:
        jmeter_exec = os.path.join(jmeter_path, 'jmeter.bat')
    
    if firt_run:
        if os.path.exists(request_log):
            os.remove(request_log) # if there is no error, remove log
            
    command = '{} -n -t {} -l {}'.format(jmeter_exec, request_file, request_log)
    #python_command = 'jmeter.bat -n -t 
    # run_command
    os.popen(command)
    time.sleep(10)
    success = _get_result_from_log(request_log)
    
    if not success:
        if firt_run:
            # raise error
            logging.error("Error in init first time run _get_request_by_type")
            raise Exception('Unexpected failure in init, please check!!!!!!!!')
        else:
            # log and return None
            # log
            logging.info("Failure happen and return None")
            return None
    else:
        # return set of services 
        # get trace from jaeger
        # extract services set
        return _get_trace_from_jaeger(request_type)
        
def _get_trace_from_jaeger(request_type):
    # get trace from Jaeger. If deploy in istio, we need to expose the port first. Please refer to istio Jaeger website. 
    #api_command = 'http://34.74.108.241:32688/api/traces?end=1605986668774000&limit=20&lookback=1h&maxDuration&minDuration&service=ts-basic-service&start=1605983068774000'
    limit_number = 4
    entry_service_name = request_to_entry_service[request_type]
    end_time = _get_milliseconds_time(datetime.now())
    start_time = _get_milliseconds_time(datetime.now() - timedelta(seconds = 20))
    root_url = 'https://tracing.34.75.83.128.nip.io/jaeger/'
    #root_url = 'http://34.74.108.241:32688/'
    api_url = root_url + 'api/traces?end={}&limit={}&lookback=1h&maxDuration&minDuration&service={}.default&start={}'\
            .format(end_time, limit_number, entry_service_name, start_time) # add .default for istio
    command = 'curl -s --insecure \'{}\''.format(api_url)
    print(command)
    time.sleep(5)
    proc = subprocess.Popen(command, shell=True,  stdout=subprocess.PIPE)
    json_data, error = proc.communicate()
    return _extrace_services_set_basedon_operation(request_type, json_data, False)
         
def _get_milliseconds_time(date_time):
    # change time to Jaeger api required time
    return int(date_time.timestamp() * 1000000)

def _extrace_services_set_basedon_operation(request_type, j, bfile = False): 
    # return list of services
    if bfile:
        with open(j) as f:
            data = json.load(f)['data']
    else:
        dataj = json.loads(j)
        data = dataj['data']
        f = open("{}.json".format(request_type),"w")
        js = json.dumps(dataj)
        f.write(js)
        f.close()
    #operation = request_to_operation[request_type]
    
    result = list()
    most_recent_time = 0
    for trace in data:
        
        outside_span = []
        for span in trace['spans']: # find outside span
            if not span['references']: # out most span
                outside_span = span
                break
        
        # if not outside_span or outside_span['operationName'] != operation:
        #     continue
        if not outside_span:
            logging.info("empty span. Please check")
            continue
        if outside_span['startTime'] < most_recent_time: # if happens before, ignore
            continue
        
        services_set = set()
        most_recent_time = outside_span['startTime']
        processes = trace['processes']
        for service in processes:
            services_set.add(processes[service]['serviceName'])
        result = list(services_set)
    return result

#traces = get_request_type_traces()
#j = json.dumps(traces)
#f = open("temp.json","w")
#f.write(j)
#f.close()
        
        
