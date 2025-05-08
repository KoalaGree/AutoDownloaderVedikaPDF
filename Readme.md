# Downloader Vedika

## License

This project is licensed under the Aladdin Free Public License (AFPL).  
You may use, copy, and distribute it for **non-commercial purposes only**.  
See the [LICENSE](LICENSE) file for full terms.

## Pemasangan Pemula 
1. Install Python dan Wkhtmltopdf di komputer anda jika belum terinstall
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
path_wkthmltopdf = C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe <!--  Path WKHtmlToPdf -->

[Urls]
jknurl = https://jkn-drive.bpjs-kesehatan.go.id <!--  URL JKN DRIVE -->
mlite = https://url-rs.com <!--  URL SIMRS/MLITE -->
```
5. Jalankan main.exe


