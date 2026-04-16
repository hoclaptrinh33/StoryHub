from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# ==========================================
# 1. CORE DOMAIN: TITLE & VOLUME & ITEM
# ==========================================
class Title(Base):
    __tablename__ = 'title'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    author = Column(String(255))
    publisher = Column(String(255))
    genre = Column(String(100))
    description = Column(Text)
    cover_url = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True) 

    volumes = relationship("Volume", back_populates="title")

class Volume(Base):
    __tablename__ = 'volume'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title_id = Column(Integer, ForeignKey('title.id'), nullable=False)
    volume_number = Column(Integer, nullable=False)
    isbn = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    title = relationship("Title", back_populates="volumes")
    items = relationship("Item", back_populates="volume")

    __table_args__ = (UniqueConstraint('title_id', 'volume_number', name='_title_volume_uc'),)

class Item(Base):
    __tablename__ = 'item'

    id = Column(String(50), primary_key=True) 
    volume_id = Column(Integer, ForeignKey('volume.id'), nullable=False)
    condition_level = Column(Integer, default=100)
    status = Column(String(50), default="available") 
    health_percent = Column(Integer, default=100)
    notes = Column(Text, nullable=True)
    
    reserved_by_customer_id = Column(Integer, nullable=True)
    reserved_at = Column(DateTime, nullable=True)
    reservation_expire_at = Column(DateTime, nullable=True)
    version_no = Column(Integer, default=1) 
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    volume = relationship("Volume", back_populates="items")

# ==========================================
# 2. CRM DOMAIN: CUSTOMER & RESERVATION
# ==========================================
class Customer(Base):
    __tablename__ = 'customer'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    address = Column(Text, nullable=True)
    membership_level = Column(String(50), default="standard")
    deposit_balance = Column(Integer, default=0)
    debt = Column(Integer, default=0)
    blacklist_flag = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

class Reservation(Base):
    __tablename__ = 'reservation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String(50), ForeignKey('item.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    status = Column(String(50), default="active") # active|expired|converted|cancelled
    reserved_at = Column(DateTime, default=datetime.utcnow)
    expire_at = Column(DateTime, nullable=False)
    converted_to = Column(String(50), nullable=True) # sold|rented
    created_by_user_id = Column(Integer, nullable=True)

# ==========================================
# 3. POS DOMAIN: ORDER & PAYMENT
# ==========================================
class PosOrder(Base):
    __tablename__ = 'pos_order'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=True)
    status = Column(String(50), default="draft") # draft|paid|cancelled|refunded|partially_refunded
    subtotal = Column(Integer, default=0)
    discount_type = Column(String(50), default="none") # percent|amount|none
    discount_value = Column(Integer, default=0)
    discount_total = Column(Integer, default=0)
    grand_total = Column(Integer, default=0)
    paid_total = Column(Integer, default=0)
    request_id = Column(String(100), unique=True, nullable=True) # Idempotency key
    created_by_user_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

class PosOrderItem(Base):
    __tablename__ = 'pos_order_item'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('pos_order.id'), nullable=False)
    item_id = Column(String(50), ForeignKey('item.id'), nullable=False)
    final_sell_price = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    line_total = Column(Integer, nullable=False)

class PosPayment(Base):
    __tablename__ = 'pos_payment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('pos_order.id'), nullable=False)
    method = Column(String(50), default="cash") # cash|bank_transfer|e_wallet|card
    amount = Column(Integer, nullable=False)
    paid_at = Column(DateTime, default=datetime.utcnow)

# ==========================================
# 4. RENTAL DOMAIN: CONTRACT & SETTLEMENT
# ==========================================
class RentalContract(Base):
    __tablename__ = 'rental_contract'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    status = Column(String(50), default="active") # active|partial_returned|closed|overdue|cancelled
    rent_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    deposit_total = Column(Integer, default=0)
    remaining_deposit = Column(Integer, default=0)
    debt_total = Column(Integer, default=0)
    request_id = Column(String(100), unique=True, nullable=True) # Idempotency key
    created_by_user_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

class RentalItem(Base):
    __tablename__ = 'rental_item'

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey('rental_contract.id'), nullable=False)
    item_id = Column(String(50), ForeignKey('item.id'), nullable=False)
    final_rent_price = Column(Integer, nullable=False)
    final_deposit = Column(Integer, nullable=False)
    status = Column(String(50), default="rented") # rented|returned|lost
    condition_before = Column(Text, nullable=True)
    condition_after = Column(Text, nullable=True)

class RentalSettlement(Base):
    __tablename__ = 'rental_settlement'

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey('rental_contract.id'), nullable=False)
    rental_fee = Column(Integer, default=0)
    late_fee = Column(Integer, default=0)
    damage_fee = Column(Integer, default=0)
    lost_fee = Column(Integer, default=0)
    total_fee = Column(Integer, default=0)
    deducted_from_deposit = Column(Integer, default=0)
    refund_to_customer = Column(Integer, default=0)
    remaining_debt = Column(Integer, default=0)
    settled_at = Column(DateTime, default=datetime.utcnow)

# ==========================================
# 5. SYSTEM & OPERATIONS: CACHE, BACKUP, AUDIT
# ==========================================
class MetadataCache(Base):
    __tablename__ = 'metadata_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_key = Column(String(255), unique=True, nullable=False)
    source = Column(String(100), nullable=True)
    payload_json = Column(Text, nullable=False)
    confidence = Column(Integer, nullable=True)
    cached_at = Column(DateTime, default=datetime.utcnow)
    expire_at = Column(DateTime, nullable=False)

class BackupJob(Base):
    __tablename__ = 'backup_job'

    id = Column(Integer, primary_key=True, autoincrement=True)
    backup_type = Column(String(50), default="full") # full|incremental
    status = Column(String(50), default="queued") # queued|running|success|failed
    file_path = Column(String(255), nullable=True)
    checksum = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_by_user_id = Column(Integer, nullable=True)

class AuditLog(Base):
    __tablename__ = 'audit_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_user_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    before_json = Column(Text, nullable=True)
    after_json = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    device_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
