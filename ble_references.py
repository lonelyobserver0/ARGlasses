import socket
import sys
import multiprocessing
from typing import Tuple, Union, Optional

class Server:
    """
    Handles Bluetooth RFCOMM server-side operations for connecting to a client,
    sending, and receiving data.
    """

    @staticmethod
    def connect(mac_address: str = "B8:27:EB:98:A1:9B", channel: int = 4) -> Optional[Tuple[socket.socket, socket.socket]]:
        """
        Initializes and binds a Bluetooth server socket, then waits for a client connection.

        Args:
            mac_address (str): The MAC address to bind to. Use "" for any available address.
            channel (int): The RFCOMM channel to listen on.

        Returns:
            tuple[socket.socket, socket.socket] or None: A tuple containing the server socket
            and the client socket on successful connection, None otherwise.
        """
        server_sock = None
        try:
            server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            server_sock.bind((mac_address, channel))
            server_sock.listen(1)
            print(f"Server: Waiting for connection on {mac_address}:{channel}...")

            # Blocking call: waits for a client to connect
            client_sock, client_addr = server_sock.accept()
            print(f"Server: Accepted connection from {client_addr}")
            return server_sock, client_sock
        except OSError as e:
            print(f"Server: Connection error: {e}")
            if server_sock:
                server_sock.close() # Ensure server socket is closed on failure
            return None

    @staticmethod
    def send(client_sock: socket.socket, data: str) -> bool:
        """
        Sends string data to the connected Bluetooth client.

        Args:
            client_sock (socket.socket): The connected client socket.
            data (str): The string data to send.

        Returns:
            bool: True if data was sent successfully, False otherwise.
        """
        try:
            client_sock.sendall(data.encode('utf-8')) # Use sendall for reliability
            # print(f"Server: Sent: {data}") # Uncomment for verbose sending logs
            return True
        except OSError as e:
            print(f"Server: Send error: {e}")
            return False

    @staticmethod
    def receive(client_sock: socket.socket, out_q: multiprocessing.Queue) -> None:
        """
        Continuously receives data from the connected Bluetooth client and puts it
        into a multiprocessing Queue. This method is blocking and intended to be run
        in a separate thread or process.

        Args:
            client_sock (socket.socket): The connected client socket.
            out_q (multiprocessing.Queue): The queue to put received data into.
        """
        try:
            while True:
                data = client_sock.recv(1024) # Receive up to 1024 bytes

                if not data:
                    # An empty bytes object means the client has disconnected gracefully
                    print("Server: Client disconnected gracefully.")
                    break # Exit the receive loop

                decoded_data = data.decode('utf-8')
                print(f"Server: Received: {decoded_data}")
                out_q.put(decoded_data) # Put the decoded string into the queue

        except OSError as e:
            print(f"Server: Receive error: {e}")
        except Exception as e: # Catch other unexpected errors
            print(f"Server: Unexpected error during receive: {e}")
        finally:
            print("Server: Stopping receive operation.")

    @staticmethod
    def close(server_sock: socket.socket, client_sock: socket.socket) -> None:
        """
        Closes both the client and server Bluetooth sockets.

        Args:
            server_sock (socket.socket): The server socket.
            client_sock (socket.socket): The client socket.
        """
        try:
            if client_sock:
                client_sock.close()
                print("Server: Client socket closed.")
            if server_sock:
                server_sock.close()
                print("Server: Server socket closed.")
        except OSError as e:
            print(f"Server: Error closing sockets: {e}")


class Client:
    """
    Handles Bluetooth RFCOMM client-side operations for connecting to a server,
    sending, and receiving data.
    """

    @staticmethod
    def connect(server_mac: str = "54:9A:8F:2B:E8:A4", channel: int = 4) -> Optional[socket.socket]:
        """
        Attempts to connect to a Bluetooth RFCOMM server.

        Args:
            server_mac (str): The MAC address of the server to connect to.
            channel (int): The RFCOMM channel to connect on.

        Returns:
            socket.socket or None: The connected client socket on success, None otherwise.
        """
        client_sock = None
        try:
            client_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            client_sock.connect((server_mac, channel))
            print(f"Client: Connected to {server_mac}:{channel}!")
            return client_sock
        except OSError as e:
            print(f"Client: Connection error: {e}")
            if client_sock:
                client_sock.close() # Ensure client socket is closed on failure
            return None

    @staticmethod
    def send(client_sock: socket.socket, data: str) -> bool:
        """
        Sends string data to the connected Bluetooth server.

        Args:
            client_sock (socket.socket): The connected client socket.
            data (str): The string data to send.

        Returns:
            bool: True if data was sent successfully, False otherwise.
        """
        try:
            client_sock.sendall(data.encode('utf-8')) # Use sendall for reliability
            # print(f"Client: Sent: {data}") # Uncomment for verbose sending logs
            return True
        except OSError as e:
            print(f"Client: Send error: {e}")
            return False

    @staticmethod
    def receive(client_sock: socket.socket) -> Optional[str]:
        """
        Receives data from the connected Bluetooth server. This method is blocking.

        Args:
            client_sock (socket.socket): The connected client socket.

        Returns:
            str or None: The decoded string data on success, or None if
            no data is received or the server disconnects.
        """
        try:
            data = client_sock.recv(1024) # Receive up to 1024 bytes

            if not data:
                # An empty bytes object means the server has disconnected gracefully
                print("Client: Server disconnected gracefully.")
                return None # Indicate disconnection

            decoded_data = data.decode('utf-8')
            print(f"Client: Received: {decoded_data}")
            return decoded_data

        except OSError as e:
            print(f"Client: Receive error: {e}")
            return None
        except Exception as e: # Catch other unexpected errors
            print(f"Client: Unexpected error during receive: {e}")
            return None

    @staticmethod
    def close(client_sock: socket.socket) -> None:
        """
        Closes the client Bluetooth socket.

        Args:
            client_sock (socket.socket): The client socket.
        """
        try:
            if client_sock:
                client_sock.close()
                print("Client: Disconnected.")
        except OSError as e:
            print(f"Client: Error closing socket: {e}")

