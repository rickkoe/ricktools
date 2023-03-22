import json

with open('config.json') as f:
  config = json.load(f)

customer_name = 'Prime'

try:
    print(config[customer_name]["path"])
except KeyError:
    print("Customer has not been setup in config.json")