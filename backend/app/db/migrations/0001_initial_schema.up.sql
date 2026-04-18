create table if not exists title (
   id          integer primary key,
   name        text not null,
   author      text not null,
   publisher   text,
   genre       text,
   description text,
   cover_url   text,
   created_at  text not null default current_timestamp,
   updated_at  text not null default current_timestamp,
   deleted_at  text
);

create table if not exists volume (
   id            integer primary key,
   title_id      integer not null,
   volume_number integer not null check ( volume_number > 0 ),
   isbn          text,
   retail_stock  integer not null default 0 check ( retail_stock >= 0 ),
   created_at    text not null default current_timestamp,
   updated_at    text not null default current_timestamp,
   deleted_at    text,
   foreign key ( title_id )
      references title ( id ),
   unique ( title_id,
            volume_number )
);

create table if not exists customer (
   id               integer primary key,
   name             text not null,
   phone            text not null unique,
   address          text,
   membership_level text not null default 'regular',
   deposit_balance  integer not null default 0 check ( deposit_balance >= 0 ),
   debt             integer not null default 0 check ( debt >= 0 ),
   blacklist_flag   integer not null default 0 check ( blacklist_flag in ( 0,
                                                                         1 ) ),
   created_at       text not null default current_timestamp,
   updated_at       text not null default current_timestamp,
   deleted_at       text
);

create table if not exists item (
   id                      text primary key,
   volume_id               integer not null,
   condition_level         integer not null check ( condition_level between 0 and 100 ),
   status                  text not null check ( status in ( 'available',
                                            'reserved',
                                            'rented',
                                            'lost',
                                            'maintenance' ) ),
   health_percent          integer not null default 100 check ( health_percent between 0 and 100 ),
   notes                   text,
   reserved_by_customer_id integer,
   reserved_at             text,
   reservation_expire_at   text,
   version_no              integer not null default 0 check ( version_no >= 0 ),
   created_at              text not null default current_timestamp,
   updated_at              text not null default current_timestamp,
   deleted_at              text,
   foreign key ( volume_id )
      references volume ( id ),
   foreign key ( reserved_by_customer_id )
      references customer ( id )
);

create table if not exists reservation (
   id                 integer primary key,
   item_id            text not null,
   customer_id        integer not null,
   status             text not null check ( status in ( 'active',
                                            'expired',
                                            'converted',
                                            'cancelled' ) ),
   reserved_at        text not null,
   expire_at          text not null,
   converted_to       text check ( converted_to in ( 'sold',
                                               'rented' )
       or converted_to is null ),
   created_by_user_id text not null,
   foreign key ( item_id )
      references item ( id ),
   foreign key ( customer_id )
      references customer ( id )
);

create table if not exists pos_order (
   id                 integer primary key,
   customer_id        integer,
   status             text not null check ( status in ( 'draft',
                                            'paid',
                                            'cancelled',
                                            'refunded',
                                            'partially_refunded' ) ),
   subtotal           integer not null check ( subtotal >= 0 ),
   discount_type      text not null check ( discount_type in ( 'percent',
                                                          'amount',
                                                          'none' ) ),
   discount_value     integer not null default 0 check ( discount_value >= 0 ),
   discount_total     integer not null default 0 check ( discount_total >= 0 ),
   grand_total        integer not null check ( grand_total >= 0 ),
   paid_total         integer not null default 0 check ( paid_total >= 0 ),
   request_id         text not null unique,
   created_by_user_id text not null,
   created_at         text not null default current_timestamp,
   updated_at         text not null default current_timestamp,
   deleted_at         text,
   foreign key ( customer_id )
      references customer ( id )
);

create table if not exists pos_order_item (
   id               integer primary key,
   order_id         integer not null,
   volume_id        integer not null,
   final_sell_price integer not null check ( final_sell_price >= 0 ),
   quantity         integer not null default 1 check ( quantity > 0 ),
   line_total       integer not null check ( line_total >= 0 ),
   foreign key ( order_id )
      references pos_order ( id ),
   foreign key ( volume_id )
      references volume ( id ),
   unique ( order_id,
            volume_id )
);

create table if not exists pos_payment (
   id       integer primary key,
   order_id integer not null,
   method   text not null check ( method in ( 'cash',
                                            'bank_transfer',
                                            'e_wallet',
                                            'card' ) ),
   amount   integer not null check ( amount > 0 ),
   paid_at  text not null,
   foreign key ( order_id )
      references pos_order ( id )
);

create table if not exists rental_contract (
   id                 integer primary key,
   customer_id        integer not null,
   status             text not null check ( status in ( 'active',
                                            'partial_returned',
                                            'closed',
                                            'overdue',
                                            'cancelled' ) ),
   rent_date          text not null,
   due_date           text not null,
   deposit_total      integer not null default 0 check ( deposit_total >= 0 ),
   remaining_deposit  integer not null default 0 check ( remaining_deposit >= 0 ),
   debt_total         integer not null default 0 check ( debt_total >= 0 ),
   request_id         text not null unique,
   created_by_user_id text not null,
   created_at         text not null default current_timestamp,
   updated_at         text not null default current_timestamp,
   deleted_at         text,
   foreign key ( customer_id )
      references customer ( id )
);

create table if not exists rental_item (
   id               integer primary key,
   contract_id      integer not null,
   item_id          text not null,
   final_rent_price integer not null check ( final_rent_price >= 0 ),
   final_deposit    integer not null check ( final_deposit >= 0 ),
   status           text not null check ( status in ( 'rented',
                                            'returned',
                                            'lost' ) ),
   condition_before integer not null check ( condition_before between 0 and 100 ),
   condition_after  integer check ( condition_after between 0 and 100 ),
   foreign key ( contract_id )
      references rental_contract ( id ),
   foreign key ( item_id )
      references item ( id ),
   unique ( contract_id,
            item_id )
);

create table if not exists rental_settlement (
   id                    integer primary key,
   contract_id           integer not null unique,
   rental_fee            integer not null default 0 check ( rental_fee >= 0 ),
   late_fee              integer not null default 0 check ( late_fee >= 0 ),
   damage_fee            integer not null default 0 check ( damage_fee >= 0 ),
   lost_fee              integer not null default 0 check ( lost_fee >= 0 ),
   total_fee             integer not null default 0 check ( total_fee >= 0 ),
   deducted_from_deposit integer not null default 0 check ( deducted_from_deposit >= 0 ),
   refund_to_customer    integer not null default 0 check ( refund_to_customer >= 0 ),
   remaining_debt        integer not null default 0 check ( remaining_debt >= 0 ),
   settled_at            text not null,
   foreign key ( contract_id )
      references rental_contract ( id )
);

create table if not exists metadata_cache (
   id           integer primary key,
   query_key    text not null unique,
   source       text not null,
   payload_json text not null,
   confidence   real not null check ( confidence >= 0
      and confidence <= 1 ),
   cached_at    text not null,
   expire_at    text not null
);

create table if not exists backup_job (
   id                 integer primary key,
   backup_type        text not null check ( backup_type in ( 'full',
                                                      'incremental' ) ),
   status             text not null check ( status in ( 'queued',
                                            'running',
                                            'success',
                                            'failed' ) ),
   file_path          text not null,
   checksum           text,
   error_message      text,
   started_at         text,
   finished_at        text,
   created_by_user_id text not null
);

create table if not exists audit_log (
   id            integer primary key,
   actor_user_id text,
   action        text not null,
   entity_type   text not null,
   entity_id     text not null,
   before_json   text,
   after_json    text,
   ip_address    text,
   device_id     text,
   created_at    text not null default current_timestamp
);

create index if not exists idx_item_status on
   item (
      status
   );
create index if not exists idx_item_reservation_expire on
   item (
      reservation_expire_at
   );
create index if not exists idx_item_volume_id on
   item (
      volume_id
   );
create index if not exists idx_rental_contract_status on
   rental_contract (
      status
   );
create index if not exists idx_pos_order_created_at on
   pos_order (
      created_at
   desc );
create index if not exists idx_reservation_item_status on
   reservation (
      item_id,
      status
   );
create index if not exists idx_reservation_expire_at on
   reservation (
      expire_at
   );
create index if not exists idx_audit_log_entity on
   audit_log (
      entity_type,
      entity_id
   );
create index if not exists idx_audit_log_created_at on
   audit_log (
      created_at
   desc );