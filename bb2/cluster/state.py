import os, json

class State:
    def __init__(self, path=os.path.join('.','state.json')):
        self.path = path
        self.state = {}
        if not os.path.exists(path):
            self.write()
        self.time = 0
        self.read()

    def write(self):
        result = json.dumps(self.state, sort_keys=True, indent=4)
        with open(self.path, "w") as file:
            file.write(result)
        self.time = os.path.getmtime(self.path)

    def read(self):
        if self.time == os.path.getmtime(self.path):
            return

        with open(self.path, "r") as file:
            result = file.read()
        if result:
            try:
                result = json.loads(result)
            except ValueError as err:
                print(err,self.path)
                return
            self.state = result
        else:
            self.write()
        self.time = os.path.getmtime(self.path)

    def keys(self):
        self.read()
        return self.state.keys()

    def items(self):
        self.read()
        return self.state.items()

    def pop(self, key):
        value = self.state.pop(key)
        self.write()
        return value

    def update(self, other):
        self.state.update(other)
        self.write()
        return

    def __getitem__(self, key):
        key = str(key)
        self.read()
        return self.state[key] if key in self.state else False

    def __setitem__(self, key, value):
        key = str(key)
        self.read()
        old = self.state[key] if key in self.state else False
        self.state[key] = value
        try:
            self.write()
        except TypeError as err:
            print(err,self.path)
            self.state[key] = old

    def __str__(self):
        return self.state.__str__()