INSERT INTO customers (customer_id, email, phone, full_name, address, city, province, postal_code, loyalty_tier, preferred_airline, created_at, updated_at) VALUES
('CUST-001', 'budi.santoso@gmail.com', '+6281212345678', 'Budi Santoso',
 'Jl. Merdeka No. 12, RT 03/RW 02, Kel. Menteng, Kec. Menteng', 'Jakarta Pusat', 'DKI Jakarta', '10310',
 'Gold', 'Garuda Indonesia', '2026-01-15 09:30:00+07', '2026-07-07 08:00:00+07'),

('CUST-002', 'siti.nurhaliza@yahoo.co.id', '+6282234567890', 'Siti Nurhaliza',
 'Jl. Asia Afrika No. 45, RT 01/RW 04, Kel. Braga, Kec. Sumur Bandung', 'Bandung', 'Jawa Barat', '40111',
 'Silver', 'Citilink', '2026-02-20 14:15:00+07', '2026-07-07 08:00:00+07'),

('CUST-003', 'wayan.sutedja@gmail.com', '+6287834567890', 'Wayan Sutedja',
 'Jl. Raya Ubud No. 88, RT 02/RW 01, Kel. Ubud, Kec. Ubud', 'Gianyar', 'Bali', '80571',
 'Gold', 'Garuda Indonesia', '2025-11-10 11:00:00+07', '2026-07-07 08:00:00+07'),

('CUST-004', 'dewi.lestari@gmail.com', '+6285234567890', 'Dewi Lestari',
 'Jl. Malioboro No. 17, RT 04/RW 03, Kel. Suryatmajan, Kec. Danurejan', 'Yogyakarta', 'DI Yogyakarta', '55213',
 'Silver', 'Lion Air', '2026-03-05 16:45:00+07', '2026-07-07 08:00:00+07'),

('CUST-005', 'muhammad.rizki@gmail.com', '+6281334567890', 'Muhammad Rizki',
 'Jl. Tunjungan No. 60, RT 02/RW 05, Kel. Genteng, Kec. Genteng', 'Surabaya', 'Jawa Timur', '60275',
 NULL, 'Lion Air', '2026-04-12 10:20:00+07', '2026-07-07 08:00:00+07')
ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO hotel_bookings (booking_id, customer_id, hotel_name, hotel_city, check_in_date, check_out_date, room_type, guests, amount_idr, payment_method, booking_status, booking_ts) VALUES
('HTL-20260701-000001', 'CUST-001', 'Grand Hyatt Jakarta', 'Jakarta Pusat',
 '2026-07-07', '2026-07-09', 'Deluxe King', 2, 3750000, 'Bank Transfer BCA', 'confirmed',
 '2026-07-06 14:30:00+07'),

('HTL-20260701-000002', 'CUST-002', 'Hotel Santika Bandung', 'Bandung',
 '2026-07-05', '2026-07-07', 'Superior Twin', 1, 860000, 'QRIS', 'completed',
 '2026-07-04 09:15:00+07'),

('HTL-20260701-000003', 'CUST-003', 'Padma Resort Bali', 'Gianyar',
 '2026-07-06', '2026-07-10', 'Premier Suite', 4, 4800000, 'GoPay', 'confirmed',
 '2026-07-05 11:00:00+07'),

('HTL-20260701-000004', 'CUST-004', 'Hotel Tentrem Yogyakarta', 'Yogyakarta',
 '2026-07-07', '2026-07-08', 'Deluxe Room', 2, 1500000, 'OVO', 'confirmed',
 '2026-07-06 16:45:00+07'),

('HTL-20260701-000005', 'CUST-005', 'Novotel Surabaya', 'Surabaya',
 '2026-07-04', '2026-07-06', 'Executive Room', 1, 2200000, 'Bank Transfer Mandiri', 'completed',
 '2026-07-03 08:00:00+07')
ON CONFLICT (booking_id) DO NOTHING;
