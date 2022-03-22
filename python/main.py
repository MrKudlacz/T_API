import os
import sys
import json 
from flask import Flask, jsonify, request
from waitress import serve
from flask_restful import Api, Resource
import json
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash
current_dir = os.path.dirname(os.path.realpath(__file__))
print(current_dir)
sys.path.append(current_dir)
import logger as logger

#parameters query supports - pairs parameter and function used for it's filtering
SUPPORTED_PARAMETERS = {'id':['get_order_by_id'],'currency':['get_order_by_currency'],'shipped_to':['get_order_by_shipped_to'],'cost':['get_order_by_cost'],'sysparm_offset':['offset_results'],'sysparm_limit':['limit_results']}
JSON_DATABASE_URL = os.path.join(current_dir, r'data/orders.json')
#placeholder for proper cred manager
THIS_SHOULD_BE_PROPER_CRED_MANAGER = os.path.join(current_dir, r'data/passwords.json')

#create app and api
app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()
log = logger.Log(current_dir + '\log.txt', 'Orders API')

#PUT request with authorisation
@app.route('/admin')
@app.route("/api/orders/create", methods=['PUT'])
@auth.login_required(role=['modify'])
@auth.login_required
def create_order():
    log.addLog('INFO',(f'Request PUT with parameters received : {request.data}'))  
    data_to_write = data
    new_data = json.loads(request.data) 
    #validate if received schema is the same as in current JSON
    if valid_create_body(data[0], new_data) is not True:
        log.addLog('ERROR',(f'Request PUT with parameters: {request.data} rejected - incorrect format'))  
        return jsonify({"error": f"{new_data} is incorrectly formatted"})
    #already know 'id' key exists, check if new ID
    if check_order_already_exists(data, new_data['id']) is not True:
        log.addLog('ERROR',(f'Request PUT with parameters: {request.data} rejected - order already existst'))  
        return jsonify({"error": f"{new_data} order already exists"})
    data_to_write.append(new_data)
    #try to write
    try:
        with open(JSON_DATABASE_URL, 'w') as outfile:
            json.dump(data_to_write, outfile)
        log.addLog('INFO',(f"Order: {new_data['id']} created"))  
        return jsonify({"success": f"order: {new_data['id']} created"})
    except:
        log.addLog('ERROR',(f'Request PUT with parameters: {request.data} - unknown exception'))  
        return jsonify({"error": f"can't create order: {new_data['id']}"})
        
#get with authorization
@app.route('/admin')
@app.route("/api/orders", methods=['GET'])
@auth.login_required(role=['read','modify'])
def get_order_by_parameters():  
    filtered_data = data
    filters_list = {}
    log.addLog('INFO',(f'Request GET with parameters received : {request.args}'))  
    #browse all parameters sent, check for supported, ignore others, loop through SUPPORTED_PARAMETERS to ensure execution order
    for parameter in SUPPORTED_PARAMETERS:
        if parameter in request.args:
            parameter_value = request.args.get(parameter)
            #filter data with function named after parameter
            exception, filtered_data = eval(SUPPORTED_PARAMETERS[parameter][0])(filtered_data, parameter_value)
            if exception:
                log.addLog('ERROR',(f'Request GET with parameters: {request.args} - {filtered_data}'))  
                return jsonify({"error":filtered_data})
            filters_list[parameter] = parameter_value
    #create response with filtered data
    number_of_search_results = len(filtered_data)
    complete_response = {
        "results":number_of_search_results,
        "filters":json.dumps(filters_list),
        "orders":filtered_data
    }
    log.addLog('INFO',(f'Request GET with parameters completed : {request.args}'))  
    return jsonify(complete_response)
@auth.verify_password
def verify_password(username, password):
    #password veryfier
    if username in users_dict:
        if check_password_hash(users_dict[username]['password'],password):
            return username
    log.addLog('INFO',(f'Failed login attempt for user: {username}'))  
@auth.get_user_roles
def get_user_roles(username):
    #get user role from name
    return users_dict[username]['role']
    
def get_order_by_id(data, order_id):
    #split orders by ,
    order_id_list = order_id.split(',')
    #check if correct no of digits and integer
    if valid_order_id(order_id_list) is not True:
        return True, f"{order_id_list} is incorrectly formatted"
    new_data = list(order for order in data if order["id"] in order_id_list)
    return False, new_data
def get_order_by_currency(data, currency):
    #split currency by ,
    currency_list = currency.split(',')
    #check if correct no of letters
    if valid_order_currency(currency_list) is not True:
        return True, f"{currency_list} is incorrectly formatted"
    new_data = list(order for order in data if order["currency"] in currency_list)
    return False, new_data
def get_order_by_shipped_to(data, shipped_to):
    #split shipped_to by ,
    shipped_to_list = shipped_to.split(',')
    new_data = list(order for order in data if (
        order["customer"]["shipping_address"]['city'] in shipped_to_list or 
        order["customer"]["shipping_address"]['county'] in shipped_to_list or 
        order["customer"]["shipping_address"]['postcode'] in shipped_to_list or 
        order["customer"]["shipping_address"]['street'] in shipped_to_list))
    return False, new_data
def get_order_by_cost(data, cost):
    #check if float
    if valid_order_id(cost) is not True:
        return True, f"{cost} is incorrectly formatted"
    cost_float = float(cost)
    new_data = list(order for order in data if float(order["price"]) >= cost_float)
    return False, new_data
def limit_results(data, number_of_orders):
    return False, data[:int(number_of_orders)]
def offset_results(data, number_of_skipped_orders):
    return False, data[int(number_of_skipped_orders):]
def valid_order_currency(currency) -> bool:
    for curr in currency:
        try:
            if len(curr) == 3:
                pass
            else:
                return False
        except ValueError:
            return False
    return True
def valid_order_id(order_id) -> bool:
    for id in order_id:
        try:
            int(id, 16)
        except ValueError:
            return False
    return True
def valid_order_cost(order_id: str) -> bool:
    try:
        if float(order_id) >=0:
            return True
        else:
            return False
    except ValueError:
        return False
def valid_create_body(sample_data, create_body) -> bool:
    try:
        #recursively check keys are the same and contain data of the same type:
        return compare_keys_rec(sample_data, create_body)
    except ValueError:
        return False    
def check_order_already_exists(data, id):
    #already know 'id' key exists
    try:
        _, existing_order = get_order_by_id(data, id)
        if len(existing_order) > 0:
            return False
        else:
            return True
    except ValueError:
        return False   
def compare_keys_rec(dictionary1, dictionary2):
    #check if outer level keys are the same
    if dictionary1.keys() != dictionary2.keys():
        return False
    #we arleady know jeys are the same - can loop only one dict
    for i_key in dictionary1.keys():
        print(i_key + 'type: ' + str(type(dictionary1[i_key])))
        if type(dictionary1[i_key]) !=  type(dictionary2[i_key]):
            return False
        #already know type is the same - can check only one type
        if type(dictionary1[i_key]) is dict:
            if not compare_keys_rec(dictionary1[i_key],dictionary2[i_key]):
                return False
    return True

if __name__ == '__main__':
    #get users credentials
    with open(THIS_SHOULD_BE_PROPER_CRED_MANAGER) as json_file:
        users = json.load(json_file) 
        users_dict = {users[i]['user']: users[i]['data'] for i in range(0, len(users))}
    #load orders data
    with open(JSON_DATABASE_URL) as json_file:
        data = json.load(json_file)
    #start serving
    api.add_resource(Resource)
    serve(app, host = '0.0.0.0', port = 5000, threads = 1)        
    