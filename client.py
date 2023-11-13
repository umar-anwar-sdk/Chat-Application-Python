import threading
import socket
import argparse
import tkinter as tk

from queue import Queue


class Send(threading.Thread):
    def __init__(self, sock, name, messages_queue):
        super().__init__()
        self.sock = sock
        self.name = name
        self.messages_queue = messages_queue

    def run(self):
        while True:
            message = self.messages_queue.get()

            if message == "QUIT":
                self.sock.sendall('Server: {} has left the chat.'.format(self.name).encode('ascii'))
                break
            else:
                self.sock.sendall('{}: {}'.format(self.name, message).encode('ascii'))

    def send_message(self, message):
        self.messages_queue.put(message)


class Receive(threading.Thread):
    def __init__(self, sock, name, messages):
        super().__init__()
        self.sock = sock
        self.name = name
        self.messages = messages

    def run(self):
        while True:
            try:
                message = self.sock.recv(1024).decode('ascii')
            except ConnectionAbortedError:
                print('\nNo. We have lost connection to the server!')
                print('\nQuitting...')
                break

            if message:
                self.messages.insert(tk.END, message)


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = None
        self.messages = None
        self.receive_thread = None
        self.send_thread = None
        self.window = None
        self.messages_queue = Queue()

    def start(self):
        print('Trying to connect to {}:{}...'.format(self.host, self.port))
        self.sock.connect((self.host, self.port))

        print('Successfully connected to {}:{}'.format(self.host, self.port))
        print()
        self.name = input('Your name: ')
        print()
        print('Welcome, {}! Getting ready to send and receive messages...'.format(self.name))

        self.send_thread = Send(self.sock, self.name, self.messages_queue)
        self.receive_thread = Receive(self.sock, self.name, self.messages)

        self.send_thread.start()
        self.receive_thread.start()

        self.sock.sendall('Server: {} has joined the chat. say whatsapp'.format(self.name).encode('ascii'))
        print('{}:'.format(self.name), end='')

        return self.receive_thread

    def send(self, message):
        self.messages_queue.put(message)

    def shutdown(self):
        self.messages_queue.put("QUIT")
        if self.send_thread:
            self.send_thread.join()
        if self.receive_thread:
            self.receive_thread.join()
        if self.window:
            self.window.destroy()


def main(host, port):
    client = Client(host, port)
    receive_thread = client.start()

    window = tk.Tk()
    window.title("Chatroom")

    frame_messages = tk.Frame(master=window)
    scrollbar = tk.Scrollbar(master=frame_messages)
    messages_listbox = tk.Listbox(master=frame_messages, yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
    messages_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    client.messages = messages_listbox
    receive_thread.messages = messages_listbox

    frame_messages.grid(row=0, column=0, columnspan=2, sticky="nesw")

    frame_entry = tk.Frame(master=window)
    text_input = tk.Entry(master=frame_entry)
    text_input.pack(fill=tk.BOTH, expand=True)
    text_input.bind("<Return>", lambda x: client.send(text_input.get()))
    text_input.insert(0, "Write your message here.")

    btn_send = tk.Button(
        master=window,
        text='Send',
        command=lambda: client.send(text_input.get())
    )

    frame_entry.grid(row=1, column=0, padx=10, sticky="ew")
    btn_send.grid(row=1, column=1, padx=10, sticky="ew")

    window.rowconfigure(0, minsize=500, weight=1)
    window.rowconfigure(1, minsize=50, weight=0)
    window.columnconfigure(0, minsize=500, weight=1)
    window.columnconfigure(1, minsize=200, weight=0)

    client.window = window
    window.protocol("WM_DELETE_WINDOW", client.shutdown)
    window.mainloop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chatroom Server")
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')

    args = parser.parse_args()
    main(args.host, args.p)
