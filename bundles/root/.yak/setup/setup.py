def configure(ports):
    ports.provide("greet", lambda: "Hello from root context!")
    print("test")
