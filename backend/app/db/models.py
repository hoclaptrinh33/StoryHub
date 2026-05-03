from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
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
    retail_stock = Column(Integer, default=0)
    p_sell_new = Column(Integer, default=0)
    
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
    item_type = Column(String(20), default="rental") # retail|rental
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
    volume_id = Column(Integer, ForeignKey('volume.id'), nullable=False)
    final_sell_price = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    line_total = Column(Integer, nullable=False)


class PriceRule(Base):
    __tablename__ = 'price_rule'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_code = Column(String(100), nullable=False)
    version_no = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)
    k_rent = Column(Float, nullable=False)
    k_deposit = Column(Float, nullable=False)
    d_floor = Column(Integer, nullable=False)
    used_demand_factor = Column(Float, nullable=False)
    used_cap_ratio = Column(Float, nullable=False)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    created_by_user_id = Column(String(50), nullable=False)
    activated_by_user_id = Column(String(50), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint('rule_code', 'version_no', name='_price_rule_version_uc'),)


class OrderItem(Base):
    __tablename__ = 'order_item'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_type = Column(String(20), nullable=False)
    pos_order_id = Column(Integer, ForeignKey('pos_order.id'), nullable=True)
    rental_contract_id = Column(Integer, ForeignKey('rental_contract.id'), nullable=True)
    pos_order_item_id = Column(Integer, ForeignKey('pos_order_item.id'), nullable=True)
    rental_item_id = Column(Integer, ForeignKey('rental_item.id'), nullable=True)
    volume_id = Column(Integer, ForeignKey('volume.id'), nullable=False)
    item_id = Column(String(50), ForeignKey('item.id'), nullable=True)
    quantity = Column(Integer, default=1)
    p_sell_new_snapshot = Column(Integer, nullable=False)
    rent_ratio_snapshot = Column(Float, nullable=True)
    deposit_ratio_snapshot = Column(Float, nullable=True)
    deposit_floor_snapshot = Column(Integer, nullable=True)
    final_sell_price = Column(Integer, nullable=True)
    final_rent_price = Column(Integer, nullable=True)
    final_deposit = Column(Integer, nullable=True)
    line_total = Column(Integer, nullable=False)
    price_rule_id = Column(Integer, ForeignKey('price_rule.id'), nullable=True)
    price_rule_version = Column(Integer, default=0)
    override_applied = Column(Boolean, default=False)
    override_reason_code = Column(String(100), nullable=True)
    override_reason_note = Column(Text, nullable=True)
    approved_by_user_id = Column(String(50), nullable=True)
    approved_via = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    actor_user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    before_json = Column(Text, nullable=True)
    after_json = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    device_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    actor = relationship("User", foreign_keys=[actor_user_id])

class InventoryLog(Base):
    __tablename__ = 'inventory_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    action_type = Column(String(50), nullable=False) # STOCK_IN, STOCK_OUT, ADJUST, CONVERT, PRICE_CHANGE
    target_type = Column(String(50), nullable=False) # VOLUME, ITEM
    target_id = Column(String(50), nullable=False)
    title_name = Column(String(255), nullable=True)
    sub_text = Column(String(255), nullable=True)
    change_qty = Column(Integer, default=0)
    old_qty = Column(Integer, nullable=True)
    new_qty = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])

# ==========================================
# 6. AUTH & USER DOMAIN
# ==========================================
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="cashier") # owner|manager|cashier
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
