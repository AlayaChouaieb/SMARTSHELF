-- SMARTSHELF demonstration dataset
-- Safe to run more than once. Uses stable SKU/batch/shelf keys.
-- Existing products and unrelated stock records are not deleted.
-- Seeded demo inventory quantities are set to the values below on each run.

BEGIN;

INSERT INTO categories (name, description) VALUES
    ('Beverages', 'Water, soft drinks and juices'),
    ('Dairy', 'Milk and chilled dairy products'),
    ('Bakery', 'Bread and baked goods'),
    ('Pantry', 'Shelf-stable grocery essentials'),
    ('Snacks', 'Packaged snack products'),
    ('Household', 'Household cleaning products'),
    ('Personal Care', 'Personal hygiene products'),
    ('Frozen Foods', 'Frozen vegetables and prepared foods')
ON CONFLICT (name) DO NOTHING;

INSERT INTO suppliers (name, contact_name, email, phone, address)
SELECT v.name, v.contact_name, v.email, v.phone, v.address
FROM (VALUES
    ('Tunisia Foods Distribution', 'Sales Desk', 'sales@tunisianfoods.example', '+216 70 100 101', 'Tunis, Tunisia'),
    ('Carthage Dairy', 'Wholesale Team', 'orders@carthagedairy.example', '+216 70 100 102', 'Ben Arous, Tunisia'),
    ('Maghreb Consumer Goods', 'Retail Support', 'support@maghrebgoods.example', '+216 70 100 103', 'Sousse, Tunisia')
) AS v(name, contact_name, email, phone, address)
WHERE NOT EXISTS (
    SELECT 1 FROM suppliers s WHERE s.name = v.name
);

INSERT INTO shelves (code, name, location, description, device_id)
VALUES
    ('SHELF-A02', 'Beverages Shelf B', 'Aisle A - Section 2', 'Soft drinks and juices', 'SIM-SHELF-002'),
    ('SHELF-B01', 'Chilled Products Shelf', 'Aisle B - Refrigerated', 'Milk and dairy products', 'SIM-SHELF-003'),
    ('SHELF-B02', 'Bakery and Pantry Shelf', 'Aisle B - Section 2', 'Bread and dry grocery products', 'SIM-SHELF-004'),
    ('SHELF-C01', 'Snacks and Household Shelf', 'Aisle C - Section 1', 'Snacks and household essentials', 'SIM-SHELF-005')
ON CONFLICT (code) DO NOTHING;

WITH product_seed(
    sku, barcode, name, brand, description, category_name, supplier_name,
    unit, selling_price, purchase_price, min_stock, max_stock
) AS (
    VALUES
    ('BEV-COLA-001', '6191000000011', 'Cola Soft Drink 1L', 'Boga', 'Carbonated cola drink, 1 litre', 'Beverages', 'Tunisia Foods Distribution', 'bottle', 2.800::numeric, 1.950::numeric, 12, 120),
    ('BEV-JUICE-001', '6191000000028', 'Orange Juice 1L', 'Ramy', 'Orange juice drink, 1 litre', 'Beverages', 'Tunisia Foods Distribution', 'carton', 3.600::numeric, 2.650::numeric, 10, 80),
    ('DAI-MILK-001', '6191000000035', 'UHT Milk 1L', 'Vitalait', 'Long-life semi-skimmed milk, 1 litre', 'Dairy', 'Carthage Dairy', 'carton', 1.650::numeric, 1.200::numeric, 20, 100),
    ('DAI-YOG-001', '6191000000042', 'Natural Yogurt 4-Pack', 'Délice', 'Four cups of plain yogurt', 'Dairy', 'Carthage Dairy', 'pack', 2.400::numeric, 1.700::numeric, 15, 90),
    ('BAK-BREAD-001', '6191000000059', 'Sliced Sandwich Bread', 'Pains du Soleil', 'Sliced white sandwich bread', 'Bakery', 'Tunisia Foods Distribution', 'loaf', 1.900::numeric, 1.250::numeric, 10, 50),
    ('PAN-PASTA-001', '6191000000066', 'Penne Pasta 500g', 'Randa', 'Durum wheat penne pasta', 'Pantry', 'Tunisia Foods Distribution', 'pack', 1.750::numeric, 1.150::numeric, 18, 120),
    ('PAN-OIL-001', '6191000000073', 'Extra Virgin Olive Oil 1L', 'Terra Delyssa', 'Extra virgin olive oil, 1 litre', 'Pantry', 'Tunisia Foods Distribution', 'bottle', 24.900::numeric, 19.500::numeric, 8, 60),
    ('PAN-TUNA-001', '6191000000080', 'Tuna in Vegetable Oil 160g', 'El Manar', 'Canned tuna, 160 grams', 'Pantry', 'Tunisia Foods Distribution', 'can', 4.200::numeric, 3.100::numeric, 12, 100),
    ('SNK-CHIPS-001', '6191000000097', 'Salted Potato Chips 150g', 'Lay’s', 'Salted potato crisps, 150 grams', 'Snacks', 'Maghreb Consumer Goods', 'bag', 2.300::numeric, 1.550::numeric, 20, 100),
    ('HOM-DETERGENT-001', '6191000000103', 'Laundry Detergent 1.5L', 'Nadhif', 'Liquid laundry detergent, 1.5 litres', 'Household', 'Maghreb Consumer Goods', 'bottle', 13.500::numeric, 9.800::numeric, 6, 40),
    ('PER-SHAMPOO-001', '6191000000110', 'Nourishing Shampoo 400ml', 'Yasmina', 'Daily care shampoo, 400 ml', 'Personal Care', 'Maghreb Consumer Goods', 'bottle', 8.900::numeric, 6.200::numeric, 8, 50),
    ('FRZ-PEAS-001', '6191000000127', 'Frozen Green Peas 1kg', 'Jardins', 'Frozen green peas, 1 kilogram', 'Frozen Foods', 'Carthage Dairy', 'bag', 6.800::numeric, 4.900::numeric, 10, 60)
),
inserted_products AS (
    INSERT INTO products (
        sku, barcode, name, brand, description, category_id, supplier_id,
        unit, selling_price, purchase_price, min_stock, max_stock
    )
    SELECT
        ps.sku, ps.barcode, ps.name, ps.brand, ps.description,
        c.id, s.id, ps.unit, ps.selling_price, ps.purchase_price,
        ps.min_stock, ps.max_stock
    FROM product_seed ps
    JOIN categories c ON c.name = ps.category_name
    JOIN suppliers s ON s.name = ps.supplier_name
    ON CONFLICT (sku) DO NOTHING
    RETURNING id
)
SELECT COUNT(*) AS newly_created_products FROM inserted_products;

WITH batch_seed(sku, batch_number, expiration_date, received_quantity, purchase_price, notes) AS (
    VALUES
    ('BEV-COLA-001', 'COLA-2026-11-A', DATE '2027-08-31', 60, 1.950::numeric, 'Demo batch - beverages'),
    ('BEV-JUICE-001', 'JUICE-2026-11-A', DATE '2026-11-28', 30, 2.650::numeric, 'Demo batch - expires soon'),
    ('DAI-MILK-001', 'MILK-2026-11-A', DATE '2026-11-22', 24, 1.200::numeric, 'Demo batch - expired stock for alert testing'),
    ('DAI-MILK-001', 'MILK-2026-11-B', DATE '2026-12-02', 36, 1.200::numeric, 'Demo batch - upcoming expiry'),
    ('DAI-YOG-001', 'YOG-2026-11-A', DATE '2026-11-23', 20, 1.700::numeric, 'Demo batch - expires today'),
    ('DAI-YOG-001', 'YOG-2026-11-B', DATE '2026-12-15', 35, 1.700::numeric, 'Demo batch - valid'),
    ('BAK-BREAD-001', 'BREAD-2026-11-A', DATE '2026-11-25', 18, 1.250::numeric, 'Demo batch - short shelf life'),
    ('PAN-PASTA-001', 'PASTA-2026-10-A', DATE '2027-10-31', 80, 1.150::numeric, 'Demo batch - pantry'),
    ('PAN-OIL-001', 'OIL-2026-09-A', DATE '2027-09-30', 24, 19.500::numeric, 'Demo batch - pantry'),
    ('PAN-TUNA-001', 'TUNA-2026-08-A', DATE '2028-08-31', 48, 3.100::numeric, 'Demo batch - canned food'),
    ('SNK-CHIPS-001', 'CHIPS-2026-11-A', DATE '2027-03-31', 16, 1.550::numeric, 'Demo batch - low stock test'),
    ('HOM-DETERGENT-001', 'DET-2026-10-A', DATE '2028-10-31', 20, 9.800::numeric, 'Demo batch - household'),
    ('PER-SHAMPOO-001', 'SHAMP-2026-10-A', DATE '2028-10-31', 28, 6.200::numeric, 'Demo batch - personal care'),
    ('FRZ-PEAS-001', 'PEAS-2026-11-A', DATE '2027-05-31', 25, 4.900::numeric, 'Demo batch - frozen')
)
INSERT INTO batches (product_id, batch_number, expiration_date, received_quantity, purchase_price, notes)
SELECT p.id, bs.batch_number, bs.expiration_date, bs.received_quantity, bs.purchase_price, bs.notes
FROM batch_seed bs
JOIN products p ON p.sku = bs.sku
ON CONFLICT (product_id, batch_number) DO NOTHING;

WITH inventory_seed(sku, batch_number, shelf_code, quantity) AS (
    VALUES
    ('BEV-COLA-001', 'COLA-2026-11-A', 'SHELF-A02', 42),
    ('BEV-JUICE-001', 'JUICE-2026-11-A', 'SHELF-A02', 7),
    ('DAI-MILK-001', 'MILK-2026-11-A', 'SHELF-B01', 5),
    ('DAI-MILK-001', 'MILK-2026-11-B', 'SHELF-B01', 22),
    ('DAI-YOG-001', 'YOG-2026-11-A', 'SHELF-B01', 8),
    ('DAI-YOG-001', 'YOG-2026-11-B', 'SHELF-B01', 18),
    ('BAK-BREAD-001', 'BREAD-2026-11-A', 'SHELF-B02', 4),
    ('PAN-PASTA-001', 'PASTA-2026-10-A', 'SHELF-B02', 35),
    ('PAN-OIL-001', 'OIL-2026-09-A', 'SHELF-B02', 11),
    ('PAN-TUNA-001', 'TUNA-2026-08-A', 'SHELF-B02', 27),
    ('SNK-CHIPS-001', 'CHIPS-2026-11-A', 'SHELF-C01', 6),
    ('HOM-DETERGENT-001', 'DET-2026-10-A', 'SHELF-C01', 13),
    ('PER-SHAMPOO-001', 'SHAMP-2026-10-A', 'SHELF-C01', 17),
    ('FRZ-PEAS-001', 'PEAS-2026-11-A', 'SHELF-C01', 9)
),
resolved_inventory AS (
    SELECT p.id AS product_id, b.id AS batch_id, sh.id AS shelf_id,
           inv.sku, inv.batch_number, inv.quantity
    FROM inventory_seed inv
    JOIN products p ON p.sku = inv.sku
    JOIN batches b ON b.product_id = p.id AND b.batch_number = inv.batch_number
    JOIN shelves sh ON sh.code = inv.shelf_code
),
upserted_inventory AS (
    INSERT INTO batch_inventory (batch_id, shelf_id, quantity)
    SELECT batch_id, shelf_id, quantity FROM resolved_inventory
    ON CONFLICT (batch_id, shelf_id)
    DO UPDATE SET quantity = EXCLUDED.quantity
    RETURNING id, batch_id, shelf_id, quantity
)
INSERT INTO inventory_events (
    product_id, batch_id, shelf_id, event_type, quantity_change,
    quantity_after, source, reference_id, notes
)
SELECT
    ri.product_id, ui.batch_id, ui.shelf_id, 'RESTOCK', ui.quantity,
    ui.quantity, 'SYSTEM',
    'DEMO-SEED-' || ri.sku || '-' || ri.batch_number,
    'Initial demonstration inventory seeded by database/seed_demo_data.sql'
FROM upserted_inventory ui
JOIN resolved_inventory ri
  ON ri.batch_id = ui.batch_id AND ri.shelf_id = ui.shelf_id
WHERE NOT EXISTS (
    SELECT 1 FROM inventory_events e
    WHERE e.reference_id = 'DEMO-SEED-' || ri.sku || '-' || ri.batch_number
);

COMMIT;

-- After running this script, refresh the alert conditions:
-- POST http://localhost:8000/api/alerts/refresh
