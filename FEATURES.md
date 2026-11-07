# AI Story Reader — Feature Specification

> **Status: BRAINSTORMING**  
> Dokumen ini mencatat rancangan dan kebutuhan fitur yang dikumpulkan dari sesi brainstorming. Poin-poin di bawah belum otomatis berarti fitur sudah tersedia atau sudah disetujui untuk implementasi. Status implementasi harus dicatat terpisah dan diperbarui ketika ada keputusan baru.

## Tujuan Produk

AI Story Reader adalah **website pribadi** untuk mengubah novel, light novel, web novel, buku digital, manga, manhwa, manhua, dan komik menjadi narasi bahasa Indonesia yang dapat dibaca dan didengarkan.

Hasil akhir yang dituju adalah website yang dapat diakses melalui browser, bukan aplikasi desktop atau aplikasi Android native.

## A. Desain Website

- Dark mode.
- Warna utama navy blue.
- Aksen biru cerah.
- Tampilan minimalis dan profesional.
- Tidak menggunakan warna ungu.
- Menghindari tampilan visual AI generik.

## B. Struktur Cerita

Struktur pengelolaan cerita yang direncanakan:

```text
Series / Judul
└── Arc atau Volume
    ├── Interlude
    ├── Chapter 1
    ├── Chapter 2
    ├── Chapter berikutnya
    ├── Ending
    └── Epilogue
```

Ketentuan:

- Series, Arc, Volume, dan Chapter merupakan entitas yang berbeda.
- Volume dan Chapter tidak boleh disamakan.
- Interlude, Ending, Epilogue, Prologue, dan bagian sejenis merupakan unit konten tersendiri.
- Satu URL yang diberikan pengguna mewakili satu Chapter atau satu bagian cerita, bukan otomatis satu Volume.
- Hubungan antarentitas harus mengikuti informasi yang benar-benar tersedia dari sumber. Sistem tidak boleh mengarang struktur cerita.

## C. Sistem Novel dan Buku Digital

- Mempertahankan seluruh isi sumber yang berhasil diperoleh.
- Tidak menyediakan mode ringkasan sebagai pengganti narasi utama.
- Menghasilkan penceritaan ulang yang detail, kronologis, dan natural dalam bahasa Indonesia.
- Mempertahankan informasi dialog, emosi, konflik, suasana, tindakan, dan perkembangan kejadian.
- Tidak mengarang kejadian, dialog, atau informasi yang tidak didukung sumber.
- Menjaga urutan kejadian sesuai sumber.
- Menyediakan teks asli dan narasi bahasa Indonesia.

## D. Sistem Komik, Manga, Manhwa, dan Manhua

Kemampuan yang direncanakan:

- Membaca halaman dan panel.
- Mengenali karakter jika bukti visual memadai.
- Membaca dialog, narasi kotak, pikiran, dan efek suara jika dapat dikenali.
- Menganalisis ekspresi wajah.
- Memahami posisi karakter dan gerakan yang terlihat.
- Menafsirkan urutan kejadian berdasarkan tata letak panel dan arah baca.
- Menghasilkan narasi untuk satu Chapter secara utuh.

Interpretasi visual harus membedakan hal yang benar-benar terlihat dari dugaan. Bagian yang tidak terbaca atau ambigu tidak boleh diisi dengan detail rekaan.

## E. Audiobook dan Pemutar Audio

Kontrol yang diinginkan:

- Play dan Pause.
- Progress bar.
- Word highlighting yang tersinkron dengan audio.
- Skip maju dan mundur 15 detik.
- Pengaturan kecepatan.
- Pengaturan suara.
- Bookmark.
- Resume otomatis dari posisi terakhir.

## F. Download Audio

- Satu Chapter menghasilkan satu berkas audio utuh.
- Format unduhan yang dituju adalah MP3.
- Interlude, Ending, Epilogue, dan bagian cerita mandiri lainnya memiliki berkas audio masing-masing.
- Tidak menyediakan download terpisah per paragraf.

## G. Jenis Input

Sumber yang direncanakan untuk didukung:

**URL**
- URL halaman Chapter atau bagian cerita.

**Dokumen**
- PDF.
- EPUB.
- TXT.
- DOCX.
- HTML.

**Gambar**
- JPG / JPEG.
- PNG.
- WEBP.

**Arsip komik**
- ZIP.
- CBZ.

Dukungan setiap format perlu diverifikasi melalui pengujian. Format yang membutuhkan OCR atau pemrosesan khusus harus memiliki alur ekstraksi dan pemeriksaan tersendiri.

## H. Story Continuity Memory

Sistem dapat menyimpan catatan konteks internal yang mencakup:

- Daftar karakter.
- Hubungan antarkarakter.
- Lokasi.
- Peristiwa sebelumnya.
- Istilah khusus.
- Konflik yang sedang berlangsung.

**Batasan penting:** Continuity Memory adalah catatan internal untuk membantu konsistensi AI. Catatan ini bukan pengganti sumber asli, tidak boleh mengesampingkan isi sumber, dan tidak boleh digunakan untuk mengisi bagian cerita yang hilang dengan asumsi.

## I. Source Verification

Sebelum narasi dianggap siap, sistem diharapkan memeriksa:

- Kelengkapan sumber yang berhasil diakses.
- Kelengkapan paragraf atau unit konten.
- Urutan paragraf, halaman, dan panel.
- Keberadaan serta urutan dialog.
- Kelengkapan narasi terhadap konten sumber.
- Kelengkapan dan hasil proses audio.

Sistem harus melaporkan ketidakpastian atau kegagalan ekstraksi. Jangan menyatakan sumber 100% lengkap jika tidak ada bukti yang cukup untuk memastikannya.

## J. Teknologi yang Dipertimbangkan

Teknologi dan layanan yang masuk dalam pertimbangan:

- GitHub untuk repository dan pengelolaan source code.
- GitHub Pages untuk hosting website statis.
- Cloudflare Workers untuk kebutuhan backend/API yang sesuai.
- HTML, CSS, dan JavaScript untuk website.
- OpenRouter.
- OpenAI API.
- Google Gemini.
- OCR.
- AI Vision.
- Text-to-Speech (TTS).

Pilihan arsitektur final belum ditetapkan. Kelayakan teknis, batas runtime, penyimpanan, keamanan secret, dan biaya setiap layanan harus diperiksa sebelum implementasi.

## K. Strategi Biaya

- Mengutamakan layanan gratis jika layak.
- Mengutamakan teknologi open-source.
- Memanfaatkan API atau layanan yang sudah dimiliki.
- Menghindari biaya langganan baru jika memungkinkan.
- Memperhitungkan biaya penggunaan API, penyimpanan, bandwidth, dan proses pembuatan audio.
- API key dan secret tidak boleh ditanam di kode frontend atau di-commit ke repository.

## L. Status dan Prinsip Pengembangan

- Status spesifikasi ini: **BRAINSTORMING**.
- Daftar ini merupakan kumpulan kebutuhan dan arah produk, bukan daftar fitur yang seluruhnya telah selesai.
- Fitur yang sudah ada dalam repository harus tetap dibedakan dari fitur yang baru direncanakan.
- Perubahan keputusan harus diperbarui dalam dokumentasi repository agar tidak hanya bergantung pada riwayat percakapan.
- Hasil akhir produk tetap berupa **website**.

## Topik Pembahasan Berikutnya

1. Sistem URL dan pengenalan sumber.
2. Ekstraksi konten dari berbagai jenis website.
3. Pengelompokan Series, Arc, Volume, dan Chapter.
4. Penanganan chapter yang terdiri dari beberapa halaman.
5. Pemeriksaan kelengkapan dan urutan sumber.
6. Batasan akses, autentikasi, dan kompatibilitas website.

---

**Catatan pemeliharaan:** Saat fitur mulai dikembangkan, tambahkan status implementasi, tautan dokumentasi teknis, dan hasil pengujian tanpa mengubah kebutuhan brainstorming menjadi klaim bahwa fitur sudah tersedia.
