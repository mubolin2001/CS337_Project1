import json
def load_data(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data
data = load_data("gg2013.json")
print(data[0])