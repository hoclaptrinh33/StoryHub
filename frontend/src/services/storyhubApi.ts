const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;

type ErrorPayload = {
  code?: string;
  message?: string;
  details?: unknown;
};

type ResponseEnvelope<T> = {
  success?: boolean;
  data?: T;
  error?: ErrorPayload;
};

type RequestOptions = RequestInit & {
  token: string;
};

export class StoryHubApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: unknown;

  constructor({
    code,
    message,
    status,
    details,
  }: {
    code: string;
    message: string;
    status: number;
    details?: unknown;
  }) {
    super(message);
    this.name = "StoryHubApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function request<T>(path: string, options: RequestOptions): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  headers.set("Authorization", `Bearer ${options.token}`);
  headers.set("X-Device-Id", "WEB-KIOSK-01");

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new StoryHubApiError({
      code: "NETWORK_ERROR",
      message: "Không thể kết nối backend. Vui lòng kiểm tra dịch vụ cục bộ.",
      status: 0,
    });
  }

  let payload: ResponseEnvelope<T> | null = null;
  try {
    payload = (await response.json()) as ResponseEnvelope<T>;
  } catch {
    if (!response.ok) {
      throw new StoryHubApiError({
        code: "HTTP_ERROR",
        message: `Yêu cầu thất bại với mã ${response.status}.`,
        status: response.status,
      });
    }
  }

  if (!payload) {
    throw new StoryHubApiError({
      code: "INVALID_RESPONSE",
      message: "Phản hồi backend không hợp lệ.",
      status: response.status,
    });
  }

  if (!response.ok || payload.success === false || payload.data === undefined) {
    throw new StoryHubApiError({
      code: payload.error?.code ?? "UNKNOWN_ERROR",
      message:
        payload.error?.message ?? `Yêu cầu thất bại với mã ${response.status}.`,
      status: response.status,
      details: payload.error?.details,
    });
  }

  return payload.data;
}

export type PosSplitPaymentMethod =
  | "cash"
  | "bank_transfer"
  | "e_wallet"
  | "card";

export type PosSplitPayment = {
  method: PosSplitPaymentMethod;
  amount: number;
};

export type UnifiedCheckoutRequest = {
  customer_id: number | null;
  scanned_codes: string[];
  discount_type: "none" | "percent" | "amount";
  discount_value: number;
  split_payments: PosSplitPayment[];
  rental_days: number;
  request_id: string;
};

export type UnifiedCheckoutPayload = {
  order_id: string | null;
  rental_contract_id: string | null;
  total_sales: number;
  total_rentals: number;
  total_deposit: number;
  grand_total: number;
  request_id: string;
};

export type CheckoutInvoiceTransactionType = "sale" | "rental";

export type CheckoutInvoiceLineItem = {
  item_code: string;
  title: string;
  transaction_kind: CheckoutInvoiceTransactionType;
  quantity: number;
  unit_price: number;
  deposit: number;
  line_total: number;
};

export type CheckoutInvoicePaymentLine = {
  method: PosSplitPaymentMethod;
  amount: number;
};

export type CheckoutInvoicePayload = {
  invoice_key: string;
  transaction_type: CheckoutInvoiceTransactionType;
  order_id: string | null;
  rental_contract_id: string | null;
  customer_name: string;
  customer_phone: string | null;
  created_at: string;
  due_date: string | null;
  status: string;
  subtotal_sales: number;
  subtotal_rentals: number;
  total_deposit: number;
  penalty_total: number;
  grand_total: number;
  lines: CheckoutInvoiceLineItem[];
  payments: CheckoutInvoicePaymentLine[];
};

export type CustomerListItem = {
  id: number;
  name: string;
  phone: string;
  membership_level: string;
  deposit_balance: number;
  debt: number;
  blacklist_flag: boolean;
};

export type UpsertCustomerRequest = {
  name: string;
  membership_level: "standard" | "silver" | "gold" | "vip" | "regular";
  address?: string;
  deposit_delta?: number;
  debt_delta?: number;
  blacklist_flag?: boolean;
  request_id: string;
  phone?: string;
};

export type UpsertCustomerPayload = {
  customer_id: string;
  phone: string;
  name: string;
  membership_level: string;
  deposit_balance: number;
  debt: number;
  blacklist_flag: boolean;
  updated_at: string;
};

export type InventoryItemListItem = {
  id: string;
  volume_id?: number | null;
  name: string;
  code: string;
  price: number;
  stock_quantity?: number | null;
  status: string;
  type: "retail" | "rental";
};

export type ConvertToRentalRequest = {
  volume_id: number;
  quantity: number;
  request_id: string;
};


export type CreateVolumeRequest = {
  title_name: string;
  author: string;
  description: string;
  cover_url: string | null;
  publisher: string | null;
  categories: string[];
  page_count: number | null;
  published_date: string | null;
  volume_number: number;
  isbn: string;
  p_sell_new: number;
  retail_stock: number;
  request_id: string;
};

export type TitleMutateRequest = {
  name: string;
  author: string | null;
  description: string | null;
  genre: string | null;
  publisher: string | null;
  cover_url: string | null;
  request_id: string;
};

export type VolumeMutateRequest = {
  volume_number: number;
  isbn: string | null;
  p_sell_new: number;
  retail_stock: number;
  request_id: string;
};

export type ItemCreateRequest = {
  volume_id: number;
  id: string | null;
  item_type: "retail" | "rental";
  condition_level: number;
  notes: string | null;
  version_no: number;
  request_id: string;
};

export type ItemUpdateRequest = {
  status: string;
  item_type?: "retail" | "rental";
  condition_level: number;
  notes: string | null;
  request_id: string;
};

export type CreateVolumePayload = {
  volume_id: number;
  title_id: number;
  isbn: string;
  retail_stock: number;
};

export type UpdateVolumePriceRequest = {
  p_sell_new: number;
  request_id: string;
};

export type UpdateVolumePricePayload = {
  volume_id: number;
  isbn: string;
  old_price: number;
  new_price: number;
  updated_at: string;
};

export type ImportCoverImageRequest = {
  isbn: string;
  image_url?: string;
  image_base64?: string;
  request_id: string;
};

export type ImportCoverImagePayload = {
  cover_url: string;
  source: "url" | "base64";
};

export type ConvertToRentalPayload = {
  volume_id: number;
  converted_quantity: number;
  new_skus: string[];
};

export type RentalReturnCondition =
  | "good"
  | "minor_damage"
  | "major_damage"
  | "lost";

export type ReturnRentalItemsRequest = {
  return_lines: Array<{
    item_id: string;
    condition_after: RentalReturnCondition;
  }>;
  returned_at?: string;
  request_id: string;
};

export type ReturnRentalItemsPayload = {
  settlement_id: string;
  contract_id: string;
  rental_fee: number;
  late_fee: number;
  damage_fee: number;
  lost_fee: number;
  total_fee: number;
  deducted_from_deposit: number;
  refund_to_customer: number;
  remaining_debt: number;
  contract_status: "partial_returned" | "closed";
};

export type RentalContractPreviewPayload = {
  contract_id: string;
  customer_id: string;
  customer_name: string;
  status: "active" | "partial_returned" | "closed" | "overdue" | "cancelled";
  due_date: string;
  deposit_total: number;
  remaining_deposit: number;
  overdue_fee_per_day: number;
  damage_fee_minor_percent: number;
  damage_fee_major_percent: number;
  return_lines: Array<{
    item_id: string;
    barcode: string;
    title: string;
    rental_fee: number;
    final_deposit: number;
    overdue_days: number;
  }>;
};

export type ReturnableRentalContractListItem = {
  contract_id: string;
  customer_id: string;
  customer_name: string;
  customer_phone: string;
  status: "active" | "partial_returned" | "overdue";
  due_date: string;
  remaining_deposit: number;
  open_item_count: number;
  rented_items_preview: string;
};

export type ItemRentalStatusPayload = {
  rental_contract_id: string | null;
  item_status: string;
};

export type InventoryItemStatusPayload = {
  item_id: string;
  status: string;
  changed_at: string;
  item_type: "rental" | "retail";
};

export type MetadataAutofillRequest = {
  query_text?: string;
  isbn?: string;
  force_refresh?: boolean;
  request_id: string;
};

export type MetadataAutofillPayload = {
  source: "cache" | "external_api" | "fallback";
  cache_hit: boolean;
  metadata: {
    name: string;
    author: string;
    publisher: string;
    genre: string;
    description: string;
    cover_url: string;
    confidence: number;
  };
};

export type RevenueSummaryRequest = {
  from_date: string;
  to_date: string;
  group_by: "day" | "week" | "month";
  include_top_titles?: boolean;
  include_inventory_alert?: boolean;
  request_id: string;
};

export type RevenueTopTitle = {
  title: string;
  qty: number;
  revenue: number;
};

export type ReportTopCustomer = {
  id: number;
  name: string;
  total_transactions: number;
  total_spent: number;
};

export type ReportTransactionItem = {
  transaction_type: "sale" | "rental";
  reference_id: string;
  customer_name: string;
  amount: number;
  created_at: string;
};

export type RevenueSummaryPayload = {
  sell_revenue: number;
  rental_revenue: number;
  penalty_revenue: number;
  total_revenue: number;
  sold_items: number;
  rented_items: number;
  new_customers: number;
  top_sell_titles: RevenueTopTitle[];
  top_rent_titles: RevenueTopTitle[];
  top_customers: ReportTopCustomer[];
  recent_transactions: ReportTransactionItem[];
  inventory_alerts: Array<{
    title: string;
    available_items: number;
  }>;
};

export type CreateSystemBackupRequest = {
  backup_type: "full" | "incremental";
  include_media?: boolean;
  encryption_password_ref?: string;
  request_id: string;
};

export type BackupJobPayload = {
  backup_job_id: string;
  status: "queued" | "running" | "success" | "failed";
  file_path: string;
  checksum: string;
  created_at: string;
};

export type LatestBackupPayload = {
  backup_job_id: string;
  backup_type: "full" | "incremental";
  status: "queued" | "running" | "success" | "failed";
  file_path: string | null;
  checksum: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export type RentalSettlementStatusPayload = {
  settlement_id: string | null;
  contract_id: string;
  rental_fee: number;
  late_fee: number;
  damage_fee: number;
  lost_fee: number;
  total_fee: number;
  deducted_from_deposit: number;
  refund_to_customer: number;
  remaining_debt: number;
  settled_at: string | null;
  contract_status: "active" | "partial_returned" | "closed" | "overdue" | "cancelled";
};

export function buildRequestId(scope: string): string {
  const normalized = scope.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
  const randomPart = Math.random().toString(36).slice(2, 8);
  return `${normalized}-${Date.now()}-${randomPart}`;
}

export function resolveRealtimeWsUrl(
  token = "cashier-demo",
  branchId?: string,
): string {
  const normalizedBase = API_BASE_URL.replace(/\/+$/, "");
  const wsBase = normalizedBase.startsWith("https://")
    ? `wss://${normalizedBase.slice(8)}`
    : normalizedBase.startsWith("http://")
      ? `ws://${normalizedBase.slice(7)}`
      : normalizedBase;

  const query = new URLSearchParams({ token });
  if (branchId?.trim()) {
    query.set("branch_id", branchId.trim());
  }

  return `${wsBase}/ws/item-live-updates?${query.toString()}`;
}

export async function unifiedCheckout(
  payload: UnifiedCheckoutRequest,
  token = "cashier-demo",
): Promise<UnifiedCheckoutPayload> {
  return request<UnifiedCheckoutPayload>("/api/v1/checkout/unified", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export async function fetchCheckoutInvoice(
  transactionType: CheckoutInvoiceTransactionType,
  referenceId: string | number,
  token = "cashier-demo",
): Promise<CheckoutInvoicePayload> {
  return request<CheckoutInvoicePayload>(
    `/api/v1/checkout/invoices/${transactionType}/${encodeURIComponent(String(referenceId))}`,
    {
      method: "GET",
      token,
    },
  );
}

export async function convertToRental(
  payload: ConvertToRentalRequest,
  token = "manager-demo",
): Promise<ConvertToRentalPayload> {
  return request<ConvertToRentalPayload>("/api/v1/kho/convert-to-rental", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}


export async function createVolume(
  payload: CreateVolumeRequest,
  token = "manager-demo",
): Promise<CreateVolumePayload> {
  return request<CreateVolumePayload>("/api/v1/kho/volumes", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export async function importCoverImage(
  payload: ImportCoverImageRequest,
  token = "manager-demo",
): Promise<ImportCoverImagePayload> {
  return request<ImportCoverImagePayload>("/api/v1/kho/covers/import", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export async function updateVolumePrice(
  volumeId: number,
  payload: UpdateVolumePriceRequest,
  token = "manager-demo",
): Promise<UpdateVolumePricePayload> {
  return request<UpdateVolumePricePayload>(
    `/api/v1/kho/volumes/${volumeId}/price`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
      token,
    },
  );
}

export async function returnRentalItems(
  contractId: number,
  payload: ReturnRentalItemsRequest,
  token = "cashier-demo",
): Promise<ReturnRentalItemsPayload> {
  return request<ReturnRentalItemsPayload>(
    `/api/v1/rentals/contracts/${contractId}/return`,
    {
      method: "POST",
      body: JSON.stringify(payload),
      token,
    },
  );
}

export async function fetchRentalContractPreview(
  contractId: number,
  token = "cashier-demo",
): Promise<RentalContractPreviewPayload> {
  return request<RentalContractPreviewPayload>(`/api/v1/rentals/contracts/${contractId}`, {
    method: "GET",
    token,
  });
}

export async function checkItemRentalStatus(
  itemId: string,
  token = "cashier-demo",
): Promise<ItemRentalStatusPayload> {
  return request<ItemRentalStatusPayload>(`/api/v1/rentals/items/${encodeURIComponent(itemId)}/rental-status`, {
    method: "GET",
    token,
  });
}

export async function fetchReturnableRentalContracts(
  q?: string,
  limit = 30,
  token = "cashier-demo",
): Promise<ReturnableRentalContractListItem[]> {
  const searchParams = new URLSearchParams();
  const queryText = q?.trim();

  if (queryText) {
    searchParams.set("q", queryText);
  }
  searchParams.set("limit", String(limit));

  const queryString = searchParams.toString();
  const path = queryString
    ? `/api/v1/rentals/contracts?${queryString}`
    : "/api/v1/rentals/contracts";

  return request<ReturnableRentalContractListItem[]>(path, {
    method: "GET",
    token,
  });
}

export async function fetchCustomers(
  token = "cashier-demo",
): Promise<CustomerListItem[]> {
  return request<CustomerListItem[]>("/api/v1/customers/", {
    method: "GET",
    token,
  });
}

export async function upsertCustomer(
  phone: string,
  payload: UpsertCustomerRequest,
  token = "cashier-demo",
): Promise<UpsertCustomerPayload> {
  return request<UpsertCustomerPayload>(`/api/v1/customers/${phone}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    token,
  });
}

export async function fetchInventoryItems(
  q?: string,
  token = "cashier-demo",
): Promise<InventoryItemListItem[]> {
  const path = q ? `/api/v1/kho/items?q=${encodeURIComponent(q)}` : "/api/v1/kho/items";
  return request<InventoryItemListItem[]>(path, {
    method: "GET",
    token,
  });
}

export async function fetchInventoryItemStatus(
  itemId: string,
  token = "cashier-demo",
): Promise<InventoryItemStatusPayload> {
  return request<InventoryItemStatusPayload>(
    `/api/v1/kho/items/${encodeURIComponent(itemId)}/status`,
    {
      method: "GET",
      token,
    },
  );
}

export async function fetchRentalSettlementStatus(
  contractId: number,
  token = "cashier-demo",
): Promise<RentalSettlementStatusPayload> {
  return request<RentalSettlementStatusPayload>(
    `/api/v1/rentals/contracts/${contractId}/settlement`,
    {
      method: "GET",
      token,
    },
  );
}

export async function autofillTitleMetadata(
  payload: MetadataAutofillRequest,
  token = "cashier-demo",
): Promise<MetadataAutofillPayload> {
  return request<MetadataAutofillPayload>("/api/v1/metadata/autofill", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export async function fetchRevenueSummaryReport(
  payload: RevenueSummaryRequest,
  token = "manager-demo",
): Promise<RevenueSummaryPayload> {
  return request<RevenueSummaryPayload>("/api/v1/reports/revenue-summary", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export async function createSystemBackup(
  payload: CreateSystemBackupRequest,
  token = "manager-demo",
): Promise<BackupJobPayload> {
  return request<BackupJobPayload>("/api/v1/system/backups", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export async function fetchLatestSystemBackup(
  token = "manager-demo",
): Promise<LatestBackupPayload> {
  return request<LatestBackupPayload>("/api/v1/system/backups/latest", {
    method: "GET",
    token,
  });
}
export type LoginRequest = {
  username: string;
  password: string;
  remember_me?: boolean;
};

export type LoginPayload = {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    username: string;
    full_name: string | null;
    role: "owner" | "manager" | "cashier";
    scopes: string[];
  };
};

export async function login(payload: LoginRequest): Promise<LoginPayload> {
  const headers = new Headers();
  headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errMsg = "Đăng nhập thất bại.";
    try {
      const errPayload = await response.json();
      errMsg = errPayload.error?.message || errMsg;
    } catch {
      /* ignore */
    }
    throw new StoryHubApiError({
      code: "AUTH_FAILED",
      message: errMsg,
      status: response.status,
    });
  }

  const envelope = (await response.json()) as ResponseEnvelope<LoginPayload>;
  if (!envelope.success || !envelope.data) {
    throw new Error("Phản hồi đăng nhập không hợp lệ.");
  }
  return envelope.data;
}

// ─── Titles / Volumes / Items (Manager Kho) ─────────────────────────────────

export type TitleItem = {
  id: string;
  status: string;
  type: string;
  condition_level: number;
  notes: string | null;

  has_barcode: boolean;
  version_no: number;
  reserved_at: string | null;
  reservation_expire_at: string | null;
};

export type TitleVolume = {
  id: number;
  volume_number: number;
  isbn: string | null;
  p_sell_new: number;
  price_rental: number;   // 5% giá bán (tự động từ backend)
  price_deposit: number;  // 30% giá bán (tự động từ backend)
  retail_stock: number;
  rental_item_count: number; // số bản sao thuê available
  items: TitleItem[];
};

export type TitleEntry = {
  id: number;
  name: string;
  author: string | null;
  genre: string | null;
  publisher: string | null;
  description: string | null;
  cover_url: string | null;
  volumes: TitleVolume[];
};

export async function createTitle(payload: TitleMutateRequest): Promise<{ id: number }> {
  return request<{ id: number }>("/api/v1/kho/titles", {
    method: 'POST',
    body: JSON.stringify(payload),
    token: "manager-demo",
  });
}

export async function updateTitle(id: number, payload: TitleMutateRequest): Promise<void> {
  return request<void>(`/api/v1/kho/titles/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
    token: "manager-demo",
  });
}

export async function deleteTitle(id: number): Promise<void> {
  return request<void>(`/api/v1/kho/titles/${id}`, {
    method: 'DELETE',
    token: "manager-demo",
  });
}

export async function updateVolume(id: number, payload: VolumeMutateRequest): Promise<void> {
  return request<void>(`/api/v1/kho/volumes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
    token: "manager-demo",
  });
}

export async function deleteVolume(id: number): Promise<void> {
  return request<void>(`/api/v1/kho/volumes/${id}`, {
    method: 'DELETE',
    token: "manager-demo",
  });
}

export async function createItem(payload: ItemCreateRequest): Promise<{ id: string }> {
  return request<{ id: string }>("/api/v1/kho/items", {
    method: 'POST',
    body: JSON.stringify(payload),
    token: "manager-demo",
  });
}

export async function updateItem(id: string, payload: ItemUpdateRequest): Promise<void> {
  return request<void>(`/api/v1/kho/items/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
    token: "manager-demo",
  });
}

export async function deleteItem(id: string): Promise<void> {
  return request<void>(`/api/v1/kho/items/${id}`, {
    method: 'DELETE',
    token: "manager-demo",
  });
}

export async function fetchTitlesWithVolumes(q?: string, token = "manager-demo"): Promise<TitleEntry[]> {
  const path = q
    ? `/api/v1/kho/titles?q=${encodeURIComponent(q)}`
    : "/api/v1/kho/titles";
  return request<TitleEntry[]>(path, { method: "GET", token });
}
