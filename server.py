import socket
import os
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import unpad

# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
BUFFER_SIZE = 4096

# Load the server's private key
def load_private_key():
    try:
        with open("server_private_key.pem", "rb") as key_file:
            private_key = RSA.import_key(key_file.read())
        return private_key
    except Exception as e:
        print(f"Error loading private key: {e}")
        return None

# Decrypt the AES key using RSA
def decrypt_aes_key(encrypted_aes_key):
    try:
        private_key = load_private_key()
        if private_key is None:
            raise Exception("Private key is not loaded.")

        rsa_cipher = PKCS1_OAEP.new(private_key)
        aes_key = rsa_cipher.decrypt(encrypted_aes_key)
        return aes_key
    except Exception as e:
        print(f"Error decrypting AES key: {e}")
        return None

# Decrypt the file using the AES key
def decrypt_file_aes(encrypted_file_path, aes_key):
    try:
        with open(encrypted_file_path, "rb") as f:
            iv = f.read(16)  # Read the IV from the start of the file
            encrypted_data = f.read()

        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)

        # Save the decrypted file
        decrypted_file_path = encrypted_file_path.replace(".enc", ".dec")
        with open(decrypted_file_path, "wb") as f:
            f.write(decrypted_data)

        print(f"File decrypted successfully: {decrypted_file_path}")
        return decrypted_file_path
    except Exception as e:
        print(f"Error decrypting file: {e}")
        return None

# Handle client connections
def handle_client(client_socket):
    try:
        # Receive the file name length
        file_name_length = int.from_bytes(client_socket.recv(4), byteorder="big")
        file_name = client_socket.recv(file_name_length).decode("utf-8")
        print(f"Receiving file: {file_name}")

        # Receive the AES key length and the encrypted AES key
        aes_key_length = int.from_bytes(client_socket.recv(4), byteorder="big")
        encrypted_aes_key = client_socket.recv(aes_key_length)

        # Decrypt the AES key
        aes_key = decrypt_aes_key(encrypted_aes_key)
        if aes_key is None:
            print("Error: Failed to decrypt AES key.")
            return

        print(f"Decrypted AES key: {aes_key.hex()}")

        # Receive the encrypted file data
        encrypted_file_path = f"received_{file_name}.enc"
        with open(encrypted_file_path, "wb") as f:
            while True:
                file_data = client_socket.recv(BUFFER_SIZE)
                if not file_data:
                    break
                f.write(file_data)

        print(f"Encrypted file received and saved as: {encrypted_file_path}")

        # Decrypt the file
        decrypted_file_path = decrypt_file_aes(encrypted_file_path, aes_key)
        if decrypted_file_path:
            print(f"Decrypted file available at: {decrypted_file_path}")

    except Exception as e:
        print(f"Error handling client: {e}")

# Start the server
def start_server():
    try:
        # Load the private key before starting the server
        if load_private_key() is None:
            print("Error: Could not load private key. Ensure 'server_private_key.pem' exists.")
            return

        # Set up the server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen(5)
        print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")
            handle_client(client_socket)
            client_socket.close()

    except Exception as e:
        print(f"Error starting the server: {e}")

if __name__ == "__main__":
    start_server()
