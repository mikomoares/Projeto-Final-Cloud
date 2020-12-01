import sys
import requests
from datetime import datetime
import json
with open("URLName.txt", "r") as file:
        URL = file.readlines()
URL = "http://" + URL[0] + "/tasks/"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "get": 
            res = requests.get(URL + "getTasks")
            print(res.text)

        elif sys.argv[1] == "post" and len(sys.argv) == 4: 
            task=json.dumps({ "title": sys.argv[2],
                "pub_date": datetime.now().isoformat(),
                "description": sys.argv[3]})
            res = requests.post(URL + "postTask", data=task)
            print(res.text)
        
        elif sys.argv[1] == "post" and len(sys.argv) == 2: 
            task=json.dumps({ "title": "task",
                "pub_date": datetime.now().isoformat(),
                "description": "test"})
            res = requests.post(URL + "postTask", data=task)
            print(res.text)

        elif sys.argv[1] == "delete": 
            res = requests.delete(URL + "deleteTasks")
            print(res.text)

        else:
            print("Comando não identificado. Comandos disponiveis: get, post, delete")
    else:
        print("Comando não identificado. Comandos disponiveis: get, post, delete")