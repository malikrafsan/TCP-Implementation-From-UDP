# Tugas Besar II IF3130 - Jaringan Komputer 2022
> Pembuatan program server dan client yang dapat berkomunikasi lewat jaringan. Komunikasi menggunakan protokol "TCP-like" yang dibuat menggunakan protokol UDP. Spesifikasi untuk tugas ini dapat dilihat lebih lanjut pada [link berikut](https://docs.google.com/document/d/1uJPX2l73IROeO4pcIsNJg-FeF_uaKL_nTaPCpmdLbt0/edit#)

## Requirements
- Python 3.9.x
- Operating System Linux 
  - WSL berkemungkinan besar tidak bisa digunakan karena penggunaan auto resolve interface network

## Setup
- Clone repositori ini
  ```
  git clone https://github.com/Sister19/jarkom-ngejarkomnonstopnovember.git
  ```
- Lakukan perubahan konfigurasi program jika diperlukan, pada folder `inc`

## How to Run
- Terdapat 2 program, yaitu `client.py` dan `server.py`, maka anda memerlukan minimal 2 terminal untuk menjalankan program ini seutuhnya, anda dapat menjalankan beberapa `client.py` program secara sekaligus
- Kedua program ini tidak harus dijalankan di mesin yang sama, tetapi tentu anda perlu melalukan konfigurasi lebih lanjut agar kedua mesin dapat berkomunikasi
- Cara menjalankan
  - Server:
    1. Jalankan program server
        ```
        python3 server.py [-h] [-m] <broadcast_port> <filepath>
        ```
        - broadcast_port: port yang digunakan server
        - filepath: file yang akan dikirimkan oleh server
        - flag -m: menentukan apakah mengirimkan metadata
    2. Pilih network interface yang akan digunakan
        - pilih sesuai instruksi program
    3. Bila sudah ada client yang masuk, pilih apakah akan menunggu client lain lagi tidak
        - pilih sesuai instruksi program 
  
  - Client
    1. Jalankan program client
        ```
        client.py [-h] <client_port> <server_ip_address> <broadcast_port> <filepath>
        ```
        - client_port: port yang digunakan client
        - server_ip_address: ip address dari server
        - broadcast_port: port yang digunakan server
        - filepath: path dari file hasil kiriman server

## Developers
- Rozan Fadhil Al Hafidz | 13520039
- Malik Akbar Hashemi Rafsanjani | 13520105
- Vito Ghifari | 13520153

## References
- TCP Three way handshake - https://datatracker.ietf.org/doc/html/rfc793#section-3.4 
- TCP Connection closing - https://datatracker.ietf.org/doc/html/rfc793#section-3.5 
- Python3 socket - https://docs.python.org/3/library/socket.html 
- Python3 struct - https://docs.python.org/3/library/struct.html 
- Python3 binascii - https://docs.python.org/3/library/binascii.html 
- Python3 fcntl - https://docs.python.org/3/library/fcntl.html 
