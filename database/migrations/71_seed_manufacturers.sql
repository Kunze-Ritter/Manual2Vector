-- =====================================================
-- SEED MANUFACTURERS DATA
-- =====================================================
-- Inserts all major printer manufacturers with complete information
-- Based on series detection patterns implemented on 2025-10-09

-- Insert manufacturers (ON CONFLICT DO NOTHING to avoid duplicates)
INSERT INTO krai_core.manufacturers (
    name,
    short_name,
    country,
    founded_year,
    website,
    support_email,
    support_phone,
    logo_url,
    is_competitor,
    market_share_percent,
    annual_revenue_usd,
    employee_count,
    headquarters_address,
    stock_symbol,
    primary_business_segment,
    created_at,
    updated_at
) VALUES
-- Konica Minolta
(
    'Konica Minolta',
    'KM',
    'Japan',
    1873,
    'https://www.konicaminolta.com',
    'support@konicaminolta.com',
    '+81-3-6250-2111',
    'https://www.konicaminolta.com/favicon.ico',
    true,
    8.5,
    8900000000,
    42000,
    'Marunouchi, Chiyoda-ku, Tokyo 100-0005, Japan',
    '4902.T',
    'Office Equipment & Production Printing',
    NOW(),
    NOW()
),

-- HP (Hewlett-Packard)
(
    'Hewlett Packard',
    'HP',
    'United States',
    1939,
    'https://www.hp.com',
    'support@hp.com',
    '+1-650-857-1501',
    'https://www.hp.com/favicon.ico',
    true,
    18.2,
    63000000000,
    51000,
    '1501 Page Mill Road, Palo Alto, CA 94304, USA',
    'HPQ',
    'Technology & Printing Solutions',
    NOW(),
    NOW()
),

-- Canon
(
    'Canon',
    'Canon',
    'Japan',
    1937,
    'https://www.canon.com',
    'support@canon.com',
    '+81-3-3758-2111',
    'https://www.canon.com/favicon.ico',
    true,
    15.3,
    31000000000,
    180000,
    '30-2 Shimomaruko 3-chome, Ohta-ku, Tokyo 146-8501, Japan',
    '7751.T',
    'Imaging & Optical Products',
    NOW(),
    NOW()
),

-- Xerox
(
    'Xerox',
    'Xerox',
    'United States',
    1906,
    'https://www.xerox.com',
    'support@xerox.com',
    '+1-800-275-9376',
    'https://www.xerox.com/favicon.ico',
    true,
    12.1,
    7000000000,
    23000,
    '201 Merritt 7, Norwalk, CT 06851, USA',
    'XRX',
    'Document Management & Printing',
    NOW(),
    NOW()
),

-- Ricoh
(
    'Ricoh',
    'Ricoh',
    'Japan',
    1936,
    'https://www.ricoh.com',
    'support@ricoh.com',
    '+81-3-6278-2111',
    'https://www.ricoh.com/favicon.ico',
    true,
    10.8,
    18000000000,
    78000,
    '3-6 Nakamagome 1-chome, Ohta-ku, Tokyo 143-8555, Japan',
    '7752.T',
    'Office Imaging & Production Printing',
    NOW(),
    NOW()
),

-- Lexmark
(
    'Lexmark',
    'Lexmark',
    'United States',
    1991,
    'https://www.lexmark.com',
    'support@lexmark.com',
    '+1-859-232-2000',
    'https://www.lexmark.com/favicon.ico',
    true,
    4.2,
    3500000000,
    8500,
    '740 West New Circle Road, Lexington, KY 40550, USA',
    NULL,
    'Enterprise Printing Solutions',
    NOW(),
    NOW()
),

-- Kyocera
(
    'Kyocera',
    'Kyocera',
    'Japan',
    1959,
    'https://www.kyoceradocumentsolutions.com',
    'support@kyocera.com',
    '+81-75-604-3500',
    'https://www.kyoceradocumentsolutions.com/favicon.ico',
    true,
    6.7,
    14000000000,
    75000,
    '6 Takeda Tobadono-cho, Fushimi-ku, Kyoto 612-8501, Japan',
    '6971.T',
    'Document Solutions',
    NOW(),
    NOW()
),

-- Brother
(
    'Brother',
    'Brother',
    'Japan',
    1908,
    'https://www.brother.com',
    'support@brother.com',
    '+81-52-824-2511',
    'https://www.brother.com/favicon.ico',
    true,
    7.3,
    6500000000,
    40000,
    '15-1 Naeshiro-cho, Mizuho-ku, Nagoya 467-8561, Japan',
    '6448.T',
    'Printers & Industrial Equipment',
    NOW(),
    NOW()
),

-- Epson
(
    'Epson',
    'Epson',
    'Japan',
    1942,
    'https://www.epson.com',
    'support@epson.com',
    '+81-266-52-3131',
    'https://www.epson.com/favicon.ico',
    true,
    11.5,
    10000000000,
    77000,
    '3-5 Owa 3-chome, Suwa-shi, Nagano 392-8502, Japan',
    '6724.T',
    'Inkjet Printers & Projectors',
    NOW(),
    NOW()
),

-- OKI (OKI Data)
(
    'OKI',
    'OKI',
    'Japan',
    1881,
    'https://www.oki.com',
    'support@oki.com',
    '+81-3-3501-3111',
    'https://www.oki.com/favicon.ico',
    true,
    2.8,
    4200000000,
    17000,
    '1-7-12 Toranomon, Minato-ku, Tokyo 105-8460, Japan',
    '6703.T',
    'LED Printers & MFPs',
    NOW(),
    NOW()
),

-- Sharp
(
    'Sharp',
    'Sharp',
    'Japan',
    1912,
    'https://www.sharp.com',
    'support@sharp.com',
    '+81-6-6621-1221',
    'https://www.sharp.com/favicon.ico',
    true,
    5.4,
    21000000000,
    50000,
    '1 Takumi-cho, Sakai-ku, Sakai City, Osaka 590-8522, Japan',
    '6753.T',
    'Electronics & Office Equipment',
    NOW(),
    NOW()
),

-- Toshiba (Toshiba Tec)
(
    'Toshiba',
    'Toshiba',
    'Japan',
    1950,
    'https://www.toshibatec.com',
    'support@toshibatec.com',
    '+81-3-6830-9100',
    'https://www.toshibatec.com/favicon.ico',
    true,
    4.1,
    4800000000,
    19000,
    '1-1 Shibaura 1-chome, Minato-ku, Tokyo 105-8001, Japan',
    '6588.T',
    'Retail & Office Solutions',
    NOW(),
    NOW()
),

-- UTAX (TA Triumph-Adler)
(
    'UTAX',
    'UTAX',
    'Germany',
    1903,
    'https://www.utax.com',
    'support@utax.de',
    '+49-40-528-604-0',
    'https://www.utax.com/favicon.ico',
    true,
    1.2,
    450000000,
    1200,
    'Ohechaussee 235, 22848 Norderstedt, Germany',
    NULL,
    'Office Equipment',
    NOW(),
    NOW()
),

-- Fujifilm (Fuji Xerox)
(
    'Fujifilm',
    'Fujifilm',
    'Japan',
    1934,
    'https://www.fujifilm.com',
    'support@fujifilm.com',
    '+81-3-6271-1111',
    'https://www.fujifilm.com/favicon.ico',
    true,
    6.9,
    23000000000,
    73000,
    '7-3 Akasaka 9-chome, Minato-ku, Tokyo 107-0052, Japan',
    '4901.T',
    'Imaging & Document Solutions',
    NOW(),
    NOW()
)

ON CONFLICT (name) DO NOTHING;

-- Add comment
COMMENT ON TABLE krai_core.manufacturers IS 
'Printer and office equipment manufacturers. Seeded with 14 major manufacturers on 2025-10-09.';

-- Verify insertion
DO $$
DECLARE
    manufacturer_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO manufacturer_count FROM krai_core.manufacturers;
    RAISE NOTICE 'Total manufacturers in database: %', manufacturer_count;
END $$;
