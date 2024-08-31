import socket


class Server:
    @staticmethod
    def connect():
        server = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        
        try:
            server.bind(("B8:27:EB:98:A1:9B", 4))  # MAC Address and Channel 4
        except OSError:
            return 1, 1
        
        server.listen(1)

        print("Waiting for connection...")

        client, addr = server.accept()
        print(f"Accepted connection from {addr}")

        return server, client

    @staticmethod
    def send(client, data):
        try:
            message = data
            client.send(message.encode('utf-8'))
        except OSError:
            print("Send error")

    @staticmethod
    def receive(client, out_q):
        try:
            while True:
                data = client.recv(1024)
                if not data:
                    pass
                else:
                    output = data.decode('utf-8')
                    print(f"Received: {output}")
                    out_q.put(data)


        except OSError:
            print("Receive error")

    @staticmethod
    def close(server, client):
        client.close()
        server.close()
        print("Disconnected")


class Client:
    @staticmethod
    def connect():
        client = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        client.connect(("54:9A:8F:2B:E8:A4", 4))
        print(f"Connected!")

        return client

    @staticmethod
    def send(client, data):
        try:
            client.send(data.encode('utf-8'))

        except Exception:
            print("Send error")

    @staticmethod
    def receive(client):
        try:
            data = client.recv(1024)
            if not data:
                data = "None"
            else:
                data = data.decode('utf-8')
                print(data)
            return data

        except Exception:
            print("Receive error")

    @staticmethod
    def close(client):
        client.close()
        print("Disconnected")
