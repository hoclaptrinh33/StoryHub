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

export type CustomerListItem = {
  id: number;
  name: string;
  phone: string;
  membership_level: string;
  deposit_balance: number;
  debt: number;
  blacklist_flag: boolean;
};

export type InventoryItemListItem = {
  id: string;
  name: string;
  code: string;
  price: number;
  status: string;
  type: "retail" | "rental";
};

export type ConvertToRentalRequest = {
  volume_id: number;
  quantity: number;
  request_id: string;
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

export function buildRequestId(scope: string): string {
  const normalized = scope.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
  const randomPart = Math.random().toString(36).slice(2, 8);
  return `${normalized}-${Date.now()}-${randomPart}`;
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

export async function convertToRental(
  payload: ConvertToRentalRequest,
  token = "manager-demo",
): Promise<ConvertToRentalPayload> {
  return request<ConvertToRentalPayload>("/api/v1/inventory/convert-to-rental", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
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

export async function fetchCustomers(
  token = "cashier-demo",
): Promise<CustomerListItem[]> {
  return request<CustomerListItem[]>("/api/v1/customers/", {
    method: "GET",
    token,
  });
}

export async function fetchInventoryItems(
  token = "cashier-demo",
): Promise<InventoryItemListItem[]> {
  return request<InventoryItemListItem[]>("/api/v1/inventory/items", {
    method: "GET",
    token,
  });
}
