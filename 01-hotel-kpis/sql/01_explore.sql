-- Task 2: SQL basics. Exploring the hotel database

-- 1. First 5 rooms (R: head(rooms, 5))
SELECT *
FROM rooms
LIMIT 5;

-- 2. How many rooms of each type (R: rooms %>% count(room_type))
SELECT room_type,
       COUNT(*)           AS n_rooms,
       AVG(base_rate_eur) AS base_rate_eur
FROM rooms
GROUP BY room_type
ORDER BY n_rooms DESC;

-- 3. Long cancelled bookings (R: filter(status == "cancelled", nights >= 5))
SELECT booking_id, booking_date, check_in, nights, rate_eur, cancel_date
FROM bookings
WHERE status = 'cancelled'
  AND nights >= 5
ORDER BY rate_eur DESC
LIMIT 5;

-- 4. Bookings by status with % share (R: count(status) %>% mutate(pct = n / sum(n)))
SELECT status,
       COUNT(*) AS n_bookings,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM bookings), 1) AS pct
FROM bookings
GROUP BY status;

-- 5. Bookings and average rate per channel (R: left_join(channels) %>% group_by %>% summarise)
SELECT c.channel_name,
       c.commission_pct,
       COUNT(*)                  AS n_bookings,
       ROUND(AVG(b.rate_eur), 0) AS avg_rate_eur
FROM bookings AS b
JOIN channels AS c ON b.channel_id = c.channel_id
GROUP BY c.channel_name, c.commission_pct
ORDER BY n_bookings DESC;

-- 6. Revenue by room type, only types above 5M EUR (R: summarise then filter = HAVING)
SELECT r.room_type,
       COUNT(*)                          AS n_stays,
       ROUND(SUM(b.room_revenue_eur), 0) AS revenue_eur
FROM bookings AS b
JOIN rooms AS r ON b.room_id = r.room_id
WHERE b.status = 'stayed'
GROUP BY r.room_type
HAVING SUM(b.room_revenue_eur) > 5000000
ORDER BY revenue_eur DESC;


-- 7. Stays and average length of stay per channel (R: filter %>% group_by %>% summarise(mean(nights)))
SELECT c.channel_name,
       COUNT(*)                AS n_stays,
       ROUND(AVG(b.nights), 2) AS avg_nights
FROM bookings AS b
JOIN channels AS c ON b.channel_id = c.channel_id
WHERE b.status = 'stayed'
GROUP BY c.channel_name
ORDER BY avg_nights DESC;

