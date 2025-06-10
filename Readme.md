# Downloader Vedika

## License

This project is licensed under the Aladdin Free Public License (AFPL).  
You may use, copy, and distribute it for **non-commercial purposes only**.  
See the [LICENSE](LICENSE) file for full terms.


## Pemasangan Pemula 
1. Install Python dan qpdf di komputer anda jika belum terinstall
```
https://github.com/qpdf/qpdf/releases

```
Note : Pastikan PATH qpdf sudah tertambah

2. Download AutoDownloader.zip yang sudah release
3. Extract Autodownloader.zip
4. Rubah app.config dan sesuaikan dengan kebutuhan
```
[Database]
Host = [host]
Port = [port] 
Database = [namadb]
User = [user]
Password = [password]

[Paths]
base_path = [Path Shared Folder, Contoh : /SHARED/NamaRS/SomeFolder]

[Urls]
jknurl = https://jkn-drive.bpjs-kesehatan.go.id <!--  URL JKN DRIVE -->
mlite = https://url-rs.com <!--  URL SIMRS/MLITE -->

<!--  UsernamePassword JKNDrive -->
[UserPass]
USERNAME = 
PASSWORD = 

```
5. Jalankan main.exe 