-- Read-only query set. Choose the database at the mysql command line.
SET SESSION time_zone = '+00:00';

SELECT 'Q01_paid_active' AS case_id;
SELECT COUNT(*) AS paid_active_orders,COUNT(DISTINCT user_id) AS paid_users,SUM(amount) AS paid_active_amount
FROM orders WHERE status='paid' AND deleted_at IS NULL;

SELECT 'Q02_count_grains' AS case_id;
SELECT COUNT(*) AS all_order_rows,COUNT(DISTINCT user_id) AS ordering_users,COUNT(paid_at) AS nonnull_paid_at FROM orders;

SELECT 'Q03_group_having' AS case_id;
SELECT user_id,COUNT(*) AS paid_orders,SUM(amount) AS paid_amount FROM orders
WHERE status='paid' AND deleted_at IS NULL GROUP BY user_id HAVING COUNT(*)>=2 ORDER BY user_id;

SELECT 'Q04_preaggregate_net' AS case_id;
-- Synthetic net = COALESCE(income,0) + recharge + gift - paid_active - approved withdrawal.
-- A NULL raw income remains visible; its zero in the net is an explicit training convention.
SELECT u.id AS user_id,u.income AS income_raw,
COALESCE(o.paid_orders,0) AS paid_orders,COALESCE(o.paid_amount,0.00) AS paid_amount,
COALESCE(w.withdrawal_amount,0.00) AS approved_withdrawal,
COALESCE(f.recharge,0.00) AS recharge,COALESCE(f.gift,0.00) AS gift,
COALESCE(u.income,0.00)+COALESCE(f.recharge,0.00)+COALESCE(f.gift,0.00)-COALESCE(o.paid_amount,0.00)-COALESCE(w.withdrawal_amount,0.00) AS synthetic_net
FROM users u
LEFT JOIN (SELECT user_id,COUNT(*) AS paid_orders,SUM(amount) AS paid_amount FROM orders
 WHERE status='paid' AND deleted_at IS NULL GROUP BY user_id) o ON o.user_id=u.id
LEFT JOIN (SELECT user_id,SUM(amount) AS withdrawal_amount FROM withdrawals
 WHERE status='approved' GROUP BY user_id) w ON w.user_id=u.id
LEFT JOIN (SELECT user_id,SUM(CASE WHEN kind='recharge' THEN amount ELSE 0.00 END) AS recharge,
 SUM(CASE WHEN kind='gift' THEN amount ELSE 0.00 END) AS gift FROM funds GROUP BY user_id) f ON f.user_id=u.id
ORDER BY u.id;

SELECT 'Q05_daily_login' AS case_id;
SELECT DATE(event_at) AS event_day,COUNT(*) AS login_rows,COUNT(DISTINCT user_id) AS active_users
FROM login_events WHERE event_at>='2024-01-01 00:00:00' AND event_at<'2024-01-03 00:00:00'
GROUP BY DATE(event_at) ORDER BY event_day;

SELECT 'Q06_active_days' AS case_id;
SELECT user_id,COUNT(DISTINCT DATE(event_at)) AS active_days FROM login_events
WHERE event_at>='2024-01-01 00:00:00' AND event_at<'2024-01-03 00:00:00'
GROUP BY user_id ORDER BY user_id;

SELECT 'Q07_character_occurrences' AS case_id;
-- Single-character tokens; divide by token length for multi-character tokens.
SELECT id AS user_id,name,CHAR_LENGTH(name)-CHAR_LENGTH(REPLACE(name,'甲','')) AS occurrences_jia,
CHAR_LENGTH(name)-CHAR_LENGTH(REPLACE(name,'_','')) AS occurrences_underscore FROM users ORDER BY id;

SELECT 'Q08_ip_unix_raw' AS case_id;
SELECT id AS event_id,ip_num AS ip_raw,INET_NTOA(ip_num) AS ip_text,event_at AS event_at_raw,
UNIX_TIMESTAMP(event_at) AS unix_utc,FROM_UNIXTIME(UNIX_TIMESTAMP(event_at)) AS utc_roundtrip
FROM login_events WHERE id IN (1,3,4,5,7,8) ORDER BY id;

SELECT 'Q09_parent_self_join' AS case_id;
SELECT c.id AS user_id,c.name AS user_name,c.parent_id AS parent_id_raw,p.name AS parent_name
FROM users c LEFT JOIN users p ON p.id=c.parent_id ORDER BY c.id;

SELECT 'Q10_hex_lengths' AS case_id;
SELECT id AS user_id,HEX(name) AS name_hex,CHAR_LENGTH(name) AS name_chars,LENGTH(name) AS name_bytes,
phone AS phone_raw,HEX(phone) AS phone_hex,CHAR_LENGTH(phone) AS phone_chars FROM users ORDER BY id;

SELECT 'Q11_items_join_inflation' AS case_id;
SELECT COUNT(*) AS joined_rows,COUNT(DISTINCT o.id) AS real_orders,SUM(o.amount) AS inflated_order_amount
FROM orders o JOIN order_items i ON i.order_id=o.id WHERE o.status='paid' AND o.deleted_at IS NULL;

SELECT 'Q12_sum_distinct_counterexample' AS case_id;
SELECT SUM(amount) AS correct_order_amount,SUM(DISTINCT amount) AS wrong_distinct_amount
FROM orders WHERE status='paid' AND deleted_at IS NULL;

SELECT 'Q13_naive_multi_join' AS case_id;
-- Wrong on purpose: two orders times two approved withdrawals create four user-1 rows.
-- Keeping child filters in ON retains users with no matching children.
SELECT u.id AS user_id,COUNT(*) AS joined_rows,COALESCE(SUM(o.amount),0.00) AS inflated_paid,
COALESCE(SUM(w.amount),0.00) AS inflated_withdrawal FROM users u
LEFT JOIN orders o ON o.user_id=u.id AND o.status='paid' AND o.deleted_at IS NULL
LEFT JOIN withdrawals w ON w.user_id=u.id AND w.status='approved'
GROUP BY u.id ORDER BY u.id;

SELECT 'Q14_null_denominators' AS case_id;
SELECT COUNT(*) AS users,COUNT(income) AS known_income_users,COUNT(phone) AS known_phone_users,
SUM(income) AS known_income_sum,CAST(AVG(income) AS DECIMAL(12,2)) AS known_income_average FROM users;

SELECT 'Q15_status_softdelete_contrast' AS case_id;
SELECT
(SELECT COUNT(*) FROM orders WHERE status='paid' AND deleted_at IS NULL) AS correct_paid_active,
(SELECT SUM(amount) FROM orders WHERE status='paid' AND deleted_at IS NULL) AS correct_amount,
(SELECT COUNT(*) FROM orders WHERE status<>'pending' AND deleted_at IS NULL) AS wrong_not_pending_count,
(SELECT SUM(amount) FROM orders WHERE status<>'pending' AND deleted_at IS NULL) AS wrong_not_pending_amount,
(SELECT COUNT(*) FROM orders WHERE status='paid') AS wrong_include_deleted_count,
(SELECT SUM(amount) FROM orders WHERE status='paid') AS wrong_include_deleted_amount;
