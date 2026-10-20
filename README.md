# KandangUlar

**Tempat Ide Berkembang, Kode Python Bergerak.**

KandangUlar adalah fondasi pengembangan aplikasi web Python yang menyatukan Django, FastAPI, Flask, dan Streamlit dalam satu proyek modular. Dirancang untuk membantu pengembang membangun aplikasi berbasis database, API layanan, ekstensi, dan dashboard dengan konfigurasi keamanan yang eksplisit.

## Fitur utama

- Administrasi dan manajemen pengguna melalui Django, termasuk ORM, migrasi, session, dan aset statis.
- API asinkron FastAPI dengan schema Pydantic, bearer token, pagination, serta dokumentasi OpenAPI khusus development.
- Factory ekstensi Flask yang terhubung ke aplikasi ASGI.
- Dashboard Streamlit terpisah dengan data demonstrasi.
- CLI `kandangular` untuk menjalankan server, dashboard, perintah Django, dan menghasilkan secret.
- Konfigurasi produksi yang menolak secret lemah atau host wildcard, Argon2, cookie aman, CSRF Django, header keamanan, serta HTTPS/HSTS.
- Pengujian integrasi, dependency lock, audit dependency, dan workflow GitHub Actions.

## Status proyek

Versi awal **0.1.0** menyediakan fondasi dan contoh integrasi yang dapat dikembangkan. Cocok sebagai titik awal prototipe dan aplikasi internal; penggunaan produksi memerlukan penyesuaian otorisasi, infrastruktur, serta pemeriksaan keamanan sesuai kebutuhan.

Fondasi aplikasi Python modular, versi 0.1.0. Menggabungkan framework melalui batas tanggung jawab yang jelas, bukan menulis ulang framework tersebut. Belum merupakan framework lengkap atau hasil audit keamanan.

| Komponen | Fungsi | Lokasi |
|---|---|---|
| Django 5.2 LTS | ORM, migrasi, pengguna, session, admin | `/`, `/admin/` |
| FastAPI | API proyek, validasi, pagination, autentikasi token | `/api/v1/projects` |
| Flask | Factory untuk ekstensi WSGI | `/plugins/status` |
| Streamlit | Dashboard data contoh, proses terpisah | `127.0.0.1:8501` |

Django dan FastAPI berbagi ORM. Flask diadaptasi dengan `asgiref.wsgi.WsgiToAsgi`. Dashboard berjalan terpisah agar lifecycle WebSocket Streamlit tetap dikelola Streamlit. Login admin Django tidak memberi akses API; API memakai bearer token layanan tersendiri.

## Mulai (Linux/macOS, Python 3.12+)

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
pip install --no-deps -e .
export KANDANGULAR_ENV=development
export KANDANGULAR_SECRET_KEY="$(kandangular secret)"
export KANDANGULAR_API_TOKEN="$(kandangular secret)"
kandangular manage migrate
kandangular manage createsuperuser
kandangular serve
```

Buka http://127.0.0.1:8000. Di terminal lain dengan virtualenv aktif, jalankan `kandangular dashboard`. CLI tidak otomatis membaca `.env`; `.env.example` menjelaskan variabel yang perlu diekspor. Simpan secret di secret manager agar tidak berubah setiap restart pada penggunaan nyata.

```sh
curl http://127.0.0.1:8000/api/v1/projects \
  -H "Authorization: Bearer $KANDANGULAR_API_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Kandang pertama","description":"Proyek contoh"}'
curl http://127.0.0.1:8000/api/v1/projects \
  -H "Authorization: Bearer $KANDANGULAR_API_TOKEN"
```

Dokumentasi API tersedia pada `/api/docs` hanya di development. Klik Authorize dan masukkan token; operasi API tetap memerlukan token. API contoh menyediakan pembuatan dan daftar proyek. Pengubahan/penghapusan tersedia bagi staf melalui admin Django.

## Keamanan dan produksi

Default lingkungan adalah **production**. Startup menolak secret kurang dari 50 karakter, token kurang dari 32 karakter, token sama dengan secret, dan host wildcard. Development harus diaktifkan eksplisit. Tersedia Argon2, validasi password, CSRF Django, cookie Secure produksi, HTTPS redirect, HSTS, validasi host pada semua rute, dan header keamanan. CSP ketat diterapkan kecuali admin dan Swagger UI yang memerlukan kebijakan tersendiri; CSP admin belum disediakan.

Sebelum produksi:

1. Pasang TLS dan reverse proxy; batasi port aplikasi ke jaringan internal. `kandangular serve` hanya mendengarkan loopback dan mengabaikan proxy headers. Untuk TLS termination jalankan Uvicorn dengan `--proxy-headers --forwarded-allow-ips` berisi IP proxy yang benar-benar dipercaya, bukan `*`. Proxy wajib mengganti header forwarded dari klien. Contoh: `uvicorn kandangular.asgi:application --host 127.0.0.1 --proxy-headers --forwarded-allow-ips=127.0.0.1`. Jangan gunakan mode development untuk mengatasi redirect HTTPS.
2. Tetapkan `KANDANGULAR_ENV=production`, secret persisten, token independen, `KANDANGULAR_ALLOWED_HOSTS=domain-anda.example`, dan `KANDANGULAR_CSRF_TRUSTED_ORIGINS=https://domain-anda.example`. HSTS mencakup subdomain dan preload; pastikan seluruh subdomain menggunakan HTTPS sebelum mengaktifkan domain produksi.
3. Jalankan `kandangular manage migrate`, `kandangular manage collectstatic --noinput`, lalu `kandangular manage check --deploy --fail-level WARNING`.
4. Terapkan rate limit di gateway untuk admin/login dan API; tambahkan MFA admin, log audit, monitoring, backup serta uji pemulihan. Ini belum termasuk dalam implementasi.
5. Token contoh adalah kredensial layanan bersama dengan hak baca/tulis seluruh proyek. Untuk multiuser, tambahkan OIDC/OAuth2, izin per pengguna, isolasi tenant dan rotasi/revokasi token sebelum menyimpan data pengguna. Jangan menaruh token di JavaScript atau URL.
6. SQLite cocok untuk lokal dan prototipe satu instance. Untuk produksi dengan banyak penulisan, tambahkan driver dan konfigurasi PostgreSQL, serta backup sesuai kebutuhan aplikasi.
7. Dashboard hanya berisi data contoh dan terikat loopback. Sebelum mempublikasikan data privat, tambahkan OIDC Streamlit, otorisasi, serta proxy TLS yang mendukung WebSocket. Jangan membuka akses dashboard tanpa perlindungan tersebut.
8. Tinjau dependency dan jalankan `pip-audit -r requirements.lock` secara rutin. Lock merekam versi yang diuji, bukan jaminan bebas kerentanan di masa mendatang.

API tidak mengaktifkan CORS lintas origin dan tidak menerima session cookie sebagai autentikasi. Ekstensi Flask contoh hanya menyediakan status publik; setiap endpoint baru yang memproses data privat harus menambahkan autentikasi dan validasi sendiri. Jangan menganggap session Django otomatis berlaku di Flask.

## Pengembangan dan pengujian

```sh
pip install -e '.[dev]'
pytest -q
kandangular manage makemigrations --check --dry-run
pip-audit -r requirements.lock
```

Modul `kandangular/web` memuat model dan admin; `api.py` memuat schema dan endpoint; `plugins.py` memuat factory Flask; `dashboard.py` memuat UI Streamlit; `asgi.py` memuat routing dan pengamanan lintas komponen. Tambahkan fitur bisnis di atas batas tersebut. Pengujian memakai database sementara dan menguji autentikasi, persistensi, validasi, CSRF, host, redirect HTTPS, dan penolakan konfigurasi produksi tidak aman.

Referensi: [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/), [integrasi WSGI FastAPI](https://fastapi.tiangolo.com/advanced/wsgi/), [konfigurasi Streamlit](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).
