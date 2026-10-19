SELECT current_database();

CREATE TABLE vendas(
	id_venda integer primary key,
	data date not null,
	produto varchar(100) not null,
	categoria varchar(50),
	quantidade int not null,
	preco_unitario numeric(10,2) not null,
	local_venda varchar(100) not null,
	loja_id int,
	canal varchar(20) not null,
	cliente_email varchar(150),
	status varchar(20),
	faturamento numeric(12,2) not null
);

select * from vendas;

create table if not exists vendas_revisao (
	id_venda integer,
	data text not null,
	produto varchar(100),
	categoria varchar(50),
	quantidade int,
	preco_unitario numeric(10,2),
	local_venda varchar(100),
	loja_id int,
	canal varchar(20) not null,
	cliente_email varchar(150),
	status varchar(20),
	motivo varchar(50) not null 
);

select * from vendas_revisao; 

create table if not exists metricas_por_produto (
    produto varchar(100) primary key,
    faturamento numeric(12,2) not null
);

select * from metricas_por_dia;

create table if not exists metricas_por_local(
	local_venda varchar(100) primary key,
	faturamento numeric(12,2) not null
);

create table if not exists metricas_por_dia(
	data date primary key,
	faturamento numeric(12,2) not null 
);

SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';