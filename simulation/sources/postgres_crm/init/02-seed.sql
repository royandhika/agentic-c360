INSERT INTO customers (full_name, email, phone, city_prov, address) VALUES
    ('Budi Santoso', 'budi.santoso@gmail.com', '+62 812-3456-7890', 'Jakarta Pusat, DKI Jakarta', 'Jl. Merdeka No. 17, RT 03/RW 02, Kel. Menteng, Kec. Menteng'),
    ('Siti Nurhaliza', 'siti.nurhaliza88@yahoo.co.id', '+62 813-9876-5432', 'Bandung, Jawa Barat', 'Jl. Cihampelas No. 45, RT 01/RW 05, Kel. Tamansari, Kec. Bandung Wetan'),
    ('Wayan Sutedja', 'wayan.sutedja@proton.me', '+62 813-1122-3344', 'Denpasar, Bali', 'Jl. Gatot Subroto No. 88, Kel. Dauh Puri, Kec. Denpasar Barat'),
    ('Dewi Lestari', 'dewi.lestari@gmail.com', '+62 856-7788-9900', 'Surabaya, Jawa Timur', 'Jl. Raya Darmo No. 12, RT 04/RW 03, Kel. Wonokromo, Kec. Wonokromo'),
    ('Muhammad Rizki', 'm.rizki@outlook.com', '+62 821-4455-6677', 'Medan, Sumatera Utara', 'Jl. Sisingamangaraja No. 33, Kel. Mesjid, Kec. Medan Kota');

INSERT INTO tickets (customer_id, subject, category, priority) VALUES
    (1, 'Paket belum sampai', 'shipping', 'normal'),
    (3, 'Permintaan pengembalian dana', 'refund', 'high');
