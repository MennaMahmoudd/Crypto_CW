import tkinter as tk
from tkinter import messagebox, filedialog
import hashlib
import os
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad
from Crypto.Random import get_random_bytes
from docx import Document 
from PyPDF2 import PdfReader, PdfWriter
from pptx import Presentation
import openpyxl
import tempfile
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import DES, PKCS1_OAEP
import socket

USER_DATA_FILE = "users.txt"
UPLOADS_DIR = "uploads"  # Directory to store uploaded files


# Ensure the uploads directory exists
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# Global variable to keep track of UI components
current_widgets = []

# Function to clear all widgets in the current UI
def clear_ui():
    for widget in current_widgets:
        widget.pack_forget()
    current_widgets.clear()

# Function to generate a salt
def generate_salt():
    return os.urandom(16)  # Generates a random salt of 16 bytes

# Function to hash password with a salt
def hash_password(password, salt):
    return hashlib.sha256(salt + password.encode()).hexdigest()

# Function to save user data (username, hashed password, and salt)
def save_user(username, hashed_password, salt):
    with open(USER_DATA_FILE, "a") as file:
        file.write(f"{username},{hashed_password},{salt.hex()}\n")


def verify_user(username, password):
    if not os.path.exists(USER_DATA_FILE):
        return False  # No users file yet

    with open(USER_DATA_FILE, "r") as file:
        for line in file:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            parts = line.split(",")
            
            if len(parts) != 3:
                print(f"Skipping invalid line: {line}")  # Log invalid lines for debugging
                continue  # Skip lines that don't have exactly 3 parts
            
            saved_username, saved_hashed_password, saved_salt = parts
            if username == saved_username:
                salt = bytes.fromhex(saved_salt)  # Convert the salt back from hex
                hashed_input_password = hash_password(password, salt)
                if hashed_input_password == saved_hashed_password:
                    return True

    return False




# Function to validate password complexity
def is_password_complex(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):  # At least one uppercase letter
        return False
    if not re.search(r"[a-z]", password):  # At least one lowercase letter
        return False
    if not re.search(r"\d", password):  # At least one digit
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_]", password):  # At least one special character
        return False
    return True

# Signup function
def signup():
    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        messagebox.showwarning("Input Error", "Both fields are required!")
        return

    if not is_password_complex(password):
        messagebox.showwarning(
            "Weak Password",
            "Password must be at least 8 characters long, contain uppercase and lowercase letters, a number, and a special character.",
        )
        return

    salt = generate_salt()  # Generate a salt for the user
    hashed_password = hash_password(password, salt)  # Hash the password with the salt
    save_user(username, hashed_password, salt)
    messagebox.showinfo("Signup Success", "Account created successfully! Please log in now.")

    # Clear the username and password fields
    entry_username.delete(0, tk.END)
    entry_password.delete(0, tk.END)
    show_login_screen()

# Login function
def login():
    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        messagebox.showwarning("Input Error", "Both fields are required!")
        return

    if verify_user(username, password):
        messagebox.showinfo("Login Success", f"Welcome, {username}!")
        show_upload_screen()  # Show the upload screen on successful login
    else:
        messagebox.showerror("Login Failed", "Invalid username or password! Please sign up if you don't have an account.")
        entry_password.delete(0, tk.END)
# Function to show login screen
def show_login_screen():
    clear_ui()
    label_title.config(text="File Manager - Please Sign Up or Log In", font=("Helvetica", 18))
    label_title.pack(pady=10)
    current_widgets.append(label_title)

    label_username.pack()
    current_widgets.append(label_username)

    entry_username.pack(pady=5)
    current_widgets.append(entry_username)

    label_password.pack()
    current_widgets.append(label_password)

    entry_password.pack(pady=5)
    current_widgets.append(entry_password)

    button_login.pack(pady=10)
    current_widgets.append(button_login)

    button_signup.pack(pady=10)
    current_widgets.append(button_signup)
    
# Function to show file upload screen
def show_upload_screen():
    clear_ui()
    label_title.config(text="File Upload", font=("Helvetica", 18))
    label_title.pack(pady=10)
    current_widgets.append(label_title)

    label_info = tk.Label(root, text="Select a file to upload", font=("Helvetica", 12))
    label_info.pack(pady=10)
    current_widgets.append(label_info)

    button_browse = tk.Button(root, text="upload file", command=upload_file, font=("Helvetica", 12))
    button_browse.pack(pady=10)
    current_widgets.append(button_browse)

    button_logout = tk.Button(root, text="Logout", command=show_login_screen, font=("Helvetica", 12))
    button_logout.pack(pady=10)
    current_widgets.append(button_logout)
    
    

def encrypt_file(file_path, destination_path):
    key = get_random_bytes(16)  # AES requires a 16-byte key
    cipher = AES.new(key, AES.MODE_CBC)  # Using CBC mode for AES encryption
    with open(file_path, 'rb') as file:
        file_data = file.read()
        encrypted_data = cipher.encrypt(pad(file_data, AES.block_size))

    with open(destination_path, 'wb') as enc_file:
        # Write the IV and the encrypted data
        enc_file.write(cipher.iv)
        enc_file.write(encrypted_data)

    # Save the key in a separate file (or database, etc.)
    key_file_path = destination_path + ".key"
    with open(key_file_path, 'wb') as key_file:
        key_file.write(key)

    return key_file_path  # Return the path to the key file


# Function to handle file upload
def upload_file():
    file_path = filedialog.askopenfilename(title="Select a file", filetypes=(("Word Files", "*.docx"), ("PDF Files", "*.pdf"), ("PowerPoint Files", "*.pptx"), ("Excel Files", "*.xlsx"), ("All Files", "*.*")))
    if file_path:
        file_name = os.path.basename(file_path)
        destination = os.path.join(UPLOADS_DIR, file_name)

        if os.path.exists(destination):
            messagebox.showwarning("File Already Uploaded", f"The file '{file_name}' has already been uploaded.")
            return
        

        with open(file_path, 'rb') as source_file:
            with open(destination, 'wb') as dest_file:
                dest_file.write(source_file.read())
                
                
        encryption_key = encrypt_file(file_path, destination)
        messagebox.showinfo("File Upload", f"File '{file_name}' uploaded successfully!")
        
# Function to show uploaded files as clickable buttons
def show_uploaded_files():
    clear_ui()
    label_title.config(text="Uploaded Files", font=("Helvetica", 18))
    label_title.pack(pady=10)
    current_widgets.append(label_title)

    # Get the list of uploaded files (excluding .key files)
    uploaded_files = [file for file in os.listdir(UPLOADS_DIR) if not file.endswith(".key")]
    
    if not uploaded_files:
        messagebox.showinfo("No Files", "No files have been uploaded yet.")
        show_upload_screen()
        return

    # Display uploaded files as clickable buttons
    for file in uploaded_files:
        file_button = tk.Button(root, text=file, font=("Helvetica", 12), command=lambda file=file: file_options(file))
        file_button.pack(pady=5)
        current_widgets.append(file_button)

    # Back button to go back to the upload screen
    button_back = tk.Button(root, text="Back", command=show_upload_screen, font=("Helvetica", 12))
    button_back.pack(pady=10)
    current_widgets.append(button_back)


    
# Function to handle the options for a selected file
def file_options(file_name):
    clear_ui()

    label_title.config(text=f"Options for {file_name}", font=("Helvetica", 18))
    label_title.pack(pady=10)
    current_widgets.append(label_title)

    # Button to delete the file
    button_delete = tk.Button(root, text="Delete File", command=lambda: delete_file(file_name), font=("Helvetica", 12))
    button_delete.pack(pady=10)
    current_widgets.append(button_delete)

    # Button to rename the file
    button_rename = tk.Button(root, text="Rename File", command=lambda: rename_file(file_name), font=("Helvetica", 12))
    button_rename.pack(pady=10)
    current_widgets.append(button_rename)
    
      # Button to edit the file (added here)
    button_edit = tk.Button(root, text="Edit File", command=lambda: edit_file_in_window(file_name), font=("Helvetica", 12))
    button_edit.pack(pady=10)
    current_widgets.append(button_edit)
    
     # Button to decrypt and download the file
    button_download_decrypt = tk.Button(root, text="Download File", command=lambda: download_decrypt_file(file_name), font=("Helvetica", 12))
    button_download_decrypt.pack(pady=10)
    current_widgets.append(button_download_decrypt)
    

    # Back button to go back to the uploaded files list
    button_back = tk.Button(root, text="Back", command=show_uploaded_files, font=("Helvetica", 12))
    button_back.pack(pady=10)
    current_widgets.append(button_back)

# Function to delete a selected file
def delete_file(file_name):
    file_path = os.path.join(UPLOADS_DIR, file_name)
    try:
        os.remove(file_path)
        messagebox.showinfo("File Deleted", f"The file '{file_name}' has been deleted successfully!")
        show_uploaded_files()  # Refresh the file list
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while deleting the file: {str(e)}")

# Function to rename a selected file
def rename_file(file_name):
    def apply_rename():
        new_name = entry_new_name.get()
        if not new_name:
            messagebox.showwarning("Invalid Name", "Please enter a valid name.")
            return
        
        old_path = os.path.join(UPLOADS_DIR, file_name)
        new_path = os.path.join(UPLOADS_DIR, new_name)
        old_key_path = old_path + ".key"
        new_key_path = new_path + ".key"

        if os.path.exists(new_path):
            messagebox.showwarning("File Exists", f"A file with the name '{new_name}' already exists.")
            return

        try:
            # Rename the file
            os.rename(old_path, new_path)
            # Rename the key file, if it exists
            if os.path.exists(old_key_path):
                os.rename(old_key_path, new_key_path)
            messagebox.showinfo("File Renamed", f"The file has been renamed to '{new_name}' successfully!")
            show_uploaded_files()  # Refresh the file list
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while renaming the file: {str(e)}")
    

    
    clear_ui()

    # Prompt for a new file name
    label_title.config(text=f"Rename {file_name}", font=("Helvetica", 18))
    label_title.pack(pady=10)
    current_widgets.append(label_title)

    label_new_name = tk.Label(root, text="Enter new file name:", font=("Helvetica", 12))
    label_new_name.pack(pady=10)
    current_widgets.append(label_new_name)

    entry_new_name = tk.Entry(root, font=("Helvetica", 12))
    entry_new_name.pack(pady=10)
    entry_new_name.insert(0, file_name)  # Set the current file name as the default
    current_widgets.append(entry_new_name)

    button_apply_rename = tk.Button(root, text="Apply Rename", command=apply_rename, font=("Helvetica", 12))
    button_apply_rename.pack(pady=10)
    current_widgets.append(button_apply_rename)

    button_cancel = tk.Button(root, text="Cancel", command=show_uploaded_files, font=("Helvetica", 12))
    button_cancel.pack(pady=10)
    current_widgets.append(button_cancel)
    
def edit_file_in_window(file_name):
    clear_ui()
    label_title.config(text=f"Edit File: {file_name}", font=("Helvetica", 18))
    label_title.pack(pady=10)
    current_widgets.append(label_title)

    file_path = os.path.join(UPLOADS_DIR, file_name)
    key_file_path = file_path + ".key"  # Path to the encryption key file

    # Create a temporary directory for decrypted files
    temp_dir = tempfile.mkdtemp()
    decrypted_file_path = os.path.join(temp_dir, file_name)

    # Decrypt the file before opening
    try:
        decrypt_file(file_path, key_file_path, decrypted_file_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to decrypt file: {e}")
        show_uploaded_files()
        return

    # Attempt to load the decrypted file
    try:
        if file_name.endswith(".docx"):
            doc = Document(decrypted_file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
        elif file_name.endswith(".pdf"):
            pdf_reader = PdfReader(decrypted_file_path)
            content = "\n".join([page.extract_text() for page in pdf_reader.pages])
        elif file_name.endswith(".pptx"):
            prs = Presentation(decrypted_file_path)
            content = "\n".join([slide.shapes.title.text if slide.shapes.title else '' for slide in prs.slides])
        elif file_name.endswith(".xlsx"):
            wb = openpyxl.load_workbook(decrypted_file_path)
            sheet = wb.active
            content = "\n".join([str(cell.value) for row in sheet.iter_rows() for cell in row])
        else:
            content = ""
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open file: {e}")
        show_uploaded_files()
        return

    # Display content in a Text widget for editing
    text_edit = tk.Text(root, wrap=tk.WORD, height=15, width=40)
    text_edit.insert(tk.END, content)
    text_edit.pack(pady=10)
    current_widgets.append(text_edit)

    # Save edits back to the encrypted file
    def save_edits_and_exit():
        new_content = text_edit.get("1.0", tk.END).strip()

        try:
            if file_name.endswith(".docx"):
                doc = Document()
                doc.add_paragraph(new_content)
                doc.save(decrypted_file_path)
            elif file_name.endswith(".pdf"):
                pdf_writer = PdfWriter()
                pdf_reader = PdfReader(decrypted_file_path)
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                # Modify content as needed
                with open(decrypted_file_path, 'wb') as f:
                    pdf_writer.write(f)
            elif file_name.endswith(".pptx"):
                prs = Presentation()
                slide = prs.slides.add_slide(prs.slide_layouts[0])
                if new_content:
                    slide.shapes.title.text = new_content
                prs.save(decrypted_file_path)
            elif file_name.endswith(".xlsx"):
                wb = openpyxl.Workbook()
                sheet = wb.active
                rows = new_content.splitlines()
                for i, row in enumerate(rows, start=1):
                    sheet[f"A{i}"] = row
                wb.save(decrypted_file_path)

            # Encrypt and save the updated file
            encrypt_file(decrypted_file_path, file_path)
            messagebox.showinfo("Success", f"File '{file_name}' has been updated!")
            root.destroy()  # Close the program after saving
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save edits: {e}")

    # Add Save and Back buttons
    button_save = tk.Button(root, text="Save Edits", command=save_edits_and_exit, font=("Helvetica", 12))
    button_save.pack(pady=10)
    current_widgets.append(button_save)

    button_back = tk.Button(root, text="Back", command=show_uploaded_files, font=("Helvetica", 12))
    button_back.pack(pady=10)
    current_widgets.append(button_back)



def decrypt_file(encrypted_file_path, key_file_path, destination_path):
    if not os.path.exists(encrypted_file_path):
        raise FileNotFoundError(f"Encrypted file not found: {encrypted_file_path}")
    if not os.path.exists(key_file_path):
        raise FileNotFoundError(f"Key file not found: {key_file_path}")

    try:
        with open(encrypted_file_path, 'rb') as enc_file:
            iv = enc_file.read(16)
            encrypted_data = enc_file.read()

        with open(key_file_path, 'rb') as key_file:
            key = key_file.read()

        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)

        with open(destination_path, 'wb') as dec_file:
            dec_file.write(decrypted_data)

        return True
    except Exception as e:
        raise RuntimeError(f"Decryption failed: {e}")


   


# Function to handle decryption and download of the file
def download_decrypt_file(file_name):
    encrypted_file_path = os.path.join(UPLOADS_DIR, file_name)
    key_file_path = encrypted_file_path + ".key"  # Assuming the key is stored with this extension
    
    # Check if the encrypted file and key file exist
    if not os.path.exists(encrypted_file_path):
        messagebox.showerror("Error", "Encrypted file not found.")
        return
    if not os.path.exists(key_file_path):
        messagebox.showerror("Error", "Key file not found.")
        return

    # Ask the user where to save the decrypted file
    decrypted_file_path = filedialog.asksaveasfilename(
        defaultextension=".dec", filetypes=[("All Files", "*.*")], title="Save Decrypted File"
    )

    if not decrypted_file_path:
        return  # User canceled the save dialog

    # Perform decryption
    if decrypt_file(encrypted_file_path, key_file_path, decrypted_file_path):
        messagebox.showinfo("Download Success", f"File successfully and saved as {decrypted_file_path}.")
    else:
        messagebox.showerror("Error", "Decryption failed.")

    # Ask user for a destination to save the decrypted file
    destination_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("DOCX Files", "*.docx"), ("All Files", "*.*")])

    if destination_path:
        success = decrypt_file(encrypted_file_path, key_file_path, destination_path)
        if success:
            messagebox.showinfo("The file is Successfully", f"File  and saved to '{destination_path}'.")
        else:
            messagebox.showerror("Decryption Failed", "Failed to decrypt the file.")



# Server address and port
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345

# Load the server public key
def load_server_public_key():
    try:
        with open('server_public_key.pem', 'rb') as key_file:
            public_key = RSA.import_key(key_file.read())
        return public_key
    except Exception as e:
        print(f"Error loading public key: {e}")
        return None

# Encrypt file using AES and the server's public RSA key
def encrypt_file_aes(file_path):
    try:
        aes_key = get_random_bytes(32)  # Generate a random AES key (256 bits)
        cipher = AES.new(aes_key, AES.MODE_CBC)

        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Pad data to be a multiple of 16 bytes (AES block size)
        padded_data = pad(file_data, AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        
        # Save the encrypted data to a file
        encrypted_file_path = file_path + ".enc"
        with open(encrypted_file_path, 'wb') as f:
            f.write(cipher.iv)  # Save the IV at the beginning of the file
            f.write(encrypted_data)

        # Load the server's public key
        server_public_key = load_server_public_key()
        if server_public_key is None:
            raise Exception("Failed to load server public key.")

        # Encrypt the AES key using the server's public key
        rsa_cipher = PKCS1_OAEP.new(server_public_key)
        encrypted_aes_key = rsa_cipher.encrypt(aes_key)

        return encrypted_file_path, encrypted_aes_key
    except Exception as e:
        print(f"Error during encryption: {e}")
        return None, None

# Function to upload and encrypt the file
def Upload_file():
    file_path = filedialog.askopenfilename(title="Select a file")
    if not file_path or not os.path.exists(file_path):
        messagebox.showwarning("File Selection", "No file selected or file does not exist.")
        return

    encrypted_file_path, encrypted_aes_key = encrypt_file_aes(file_path)
    if encrypted_file_path and encrypted_aes_key:
        messagebox.showinfo("File Encryption", f"File encrypted successfully: {encrypted_file_path}")
        send_file_to_server(encrypted_file_path, encrypted_aes_key)
    else:
        messagebox.showerror("Encryption Error", "Failed to encrypt the file.")

# Function to send the encrypted file to the server
def send_file_to_server(encrypted_file_path, encrypted_aes_key):
    try:
        # Create a socket connection to the server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))

            # Send the file name length (4 bytes)
            file_name = os.path.basename(encrypted_file_path)
            file_name_length = len(file_name).to_bytes(4, byteorder='big')
            s.sendall(file_name_length)

            # Send the file name
            s.sendall(file_name.encode('utf-8'))

            # Send the encrypted AES key (length first)
            s.sendall(len(encrypted_aes_key).to_bytes(4, byteorder='big'))  # Send the length of the AES key
            s.sendall(encrypted_aes_key)

            # Send the encrypted file data
            with open(encrypted_file_path, 'rb') as file:
                while True:
                    file_data = file.read(4096)
                    if not file_data:
                        break
                    s.sendall(file_data)

            print("File sent to server successfully!")
    except Exception as e:
        print(f"Failed to send file: {str(e)}")



# Function to show file upload screen with options
def show_upload_screen():
    clear_ui()
    label_title.config(text="File Upload", font=("Helvetica", 18))
    label_title.pack(pady=10)
    current_widgets.append(label_title)

    # Option to upload a file
    button_upload = tk.Button(root, text="Upload a File", command=upload_file, font=("Helvetica", 12))
    button_upload.pack(pady=10)
    current_widgets.append(button_upload)
    
    
    button_share = tk.Button(root, text="Select a file to share",command=Upload_file ,font=("Helvetica", 12))
    button_share.pack(pady=10)
    current_widgets.append(button_share)

    # Option to show uploaded files
    button_show_files = tk.Button(root, text="Show Uploaded Files", command=show_uploaded_files, font=("Helvetica", 12))
    button_show_files.pack(pady=10)
    current_widgets.append(button_show_files)

    # Logout button
    button_logout = tk.Button(root, text="Logout", command=show_login_screen, font=("Helvetica", 12))
    button_logout.pack(pady=10)
    current_widgets.append(button_logout)

        
# Create the main window
root = tk.Tk()
root.title("File Manager")

# Create shared widgets
label_title = tk.Label(root, text="", font=("Helvetica", 18))

label_username = tk.Label(root, text="Username", font=("Helvetica", 12))
entry_username = tk.Entry(root, font=("Helvetica", 12))

label_password = tk.Label(root, text="Password", font=("Helvetica", 12))
entry_password = tk.Entry(root, font=("Helvetica", 12), show="*")

button_login = tk.Button(root, text="Login", command=login, font=("Helvetica", 12))
button_signup = tk.Button(root, text="Sign Up", command=signup, font=("Helvetica", 12))

# Start with the login screen
show_login_screen()

root.mainloop()
