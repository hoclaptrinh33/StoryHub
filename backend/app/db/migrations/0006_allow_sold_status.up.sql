PRAGMA foreign_keys=OFF;

CREATE TABLE item_new (
    id                      text primary key,
    volume_id               integer not null,
    condition_level         integer not null check ( condition_level between 0 and 100 ),
    status                  text not null check ( status in ( 'available',
                                             'reserved',
                                             'rented',
                                             'lost',
                                             'maintenance',
                                             'sold' ) ),
    health_percent          integer not null default 100 check ( health_percent between 0 and 100 ),
    notes                   text,
    reserved_by_customer_id integer,
    reserved_at             text,
    reservation_expire_at   text,
    version_no              integer not null default 0 check ( version_no >= 0 ),
    item_type               text not null default 'rental' check ( item_type in ('retail', 'rental') ),
    created_at              text not null default current_timestamp,
    updated_at              text not null default current_timestamp,
    deleted_at              text,
    foreign key ( volume_id )
       references volume ( id ),
    foreign key ( reserved_by_customer_id )
       references customer ( id )
);

INSERT INTO item_new (id, volume_id, condition_level, status, health_percent, notes, reserved_by_customer_id, reserved_at, reservation_expire_at, version_no, item_type, created_at, updated_at, deleted_at)
SELECT id, volume_id, condition_level, status, health_percent, notes, reserved_by_customer_id, reserved_at, reservation_expire_at, version_no, item_type, created_at, updated_at, deleted_at FROM item;

DROP TABLE item;
ALTER TABLE item_new RENAME TO item;

CREATE INDEX if not exists idx_item_status on item (status);
CREATE INDEX if not exists idx_item_reservation_expire on item (reservation_expire_at);
CREATE INDEX if not exists idx_item_volume_id on item (volume_id);

PRAGMA foreign_keys=ON;
