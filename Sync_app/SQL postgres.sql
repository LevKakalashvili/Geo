set @brewery_ = 'Brabandere';
set @name_ = 'Fruh Kolsch';
set @egais_code_ = '0000000000036085093';

-- Найти определенный товар
SELECT *
FROM geo.sync_app_moyskladdbgood
WHERE 
	brewery = @brewery_ and 
	name = @name_;


SELECT *
FROM geo.sync_app_moyskladdbgood
WHERE 
	name = 'Нимфоманка';


SELECT kmgood.egais_code, kmgood.full_name, cap.capacity
FROM geo.sync_app_konturmarketdbgood as kmgood
left join geo.sync_app_capacity as cap
on cap.id = kmgood.capacity_id
where kmgood.egais_code = @egais_code_;

select *
FROM geo.sync_app_konturmarketdbgood as kmgood
left join geo.sync_app_moyskladdbgood_egais_code as comp_table
on kmgood.egais_code = comp_table.konturmarketdbgood_id
where kmgood.egais_code = @egais_code_;

-- Найти все разливные напитки, доступные к продаже
create or replace view get_availible_draft as
select
	sam.brewery,
	sam.name,
	sam2.quantity
from geo.sync_app_moyskladdbstock sam2
left join geo.sync_app_moyskladdbgood sam
on sam2.uuid_id = sam.uuid 
where
	sam2.quantity > 0 and
	sam.is_draft;

 select *
 from get_availible_draft;

-- Показать доступные остатки товаров на складе (не розлив)
create or replace view get_availible_goods_not_draft as
select
	sam.brewery,
	sam.name,
	sam2.quantity
from geo.sync_app_moyskladdbstock sam2
left join geo.sync_app_moyskladdbgood sam
on sam2.uuid_id = sam.uuid 
where
	sam2.quantity > 0 and
	not sam.is_draft
order by sam.brewery, sam.name;  


select *
from get_availible_goods_not_draft;

-- Таблица соответствия (Все не связанные товары)
select
	sam.uuid,
	sam.brewery,
	sam.name
from geo.sync_app_moyskladdbgood sam
where
	sam.uuid not in
		(
			select samec.moyskladdbgood_id
			from geo.sync_app_moyskladdbgood_egais_code samec
		)
;

-- Таблица соответствия (показать все товары)
select  sam.uuid,
		sam.brewery,
		sam.name,
		sak.egais_code,
		sak.full_name
from geo.sync_app_moyskladdbgood sam
left join geo.sync_app_moyskladdbgood_egais_code comp_table
on comp_table.moyskladdbgood_id = sam.uuid
left join geo.sync_app_konturmarketdbgood sak
on sak.egais_code = comp_table.konturmarketdbgood_id;

-- Таблица соответствия (показать только привязанные товары)
select 
	sam.brewery,
	sam.name,
	sak.full_name,
	sak.egais_code 
from geo.sync_app_moyskladdbgood_egais_code comp_table
left join geo.sync_app_moyskladdbgood sam
on sam.uuid = comp_table.moyskladdbgood_id
left join geo.sync_app_konturmarketdbgood sak
on sak.egais_code = comp_table.konturmarketdbgood_id
order by sam.brewery, sam.name, sak.egais_code;

-- Поиск дубликатов
select *, COUNT(*) AS cnt
from geo.sync_app_moyskladdbgood as msgood
where path_name <> ""
GROUP BY name, is_draft, brewery, capacity, `style`
HAVING cnt > 1;

select *
from sync_app_moyskladdbgood sam 
where sam.is_draft;

-- Проданные товары за смену
SELECT sam.full_name, sam2.quantity, sam2.demand_date 
FROM geo_db.public."Sync_app_moyskladdbgood" sam, geo_db.public."Sync_app_moyskladdbretaildemand" sam2 
WHERE sam.uuid = sam2.uuid
ORDER by full_name;

-- Посмотреть остатки по товару, через ЕГАИС код
SELECT egais_code_id , quantity  
FROM geo.Sync_app_konturmarketdbstock sak 
WHERE egais_code_id
IN (
	'0000000000039190900',
	'0000000000036902642',
	'0000000000033538592',
	'0000000000031239554',
	'0000000000040233242',
	'0000000000030747643',
	'0000000000030770129'
	);


select * from 



