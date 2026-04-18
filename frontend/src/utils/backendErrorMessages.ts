const ERROR_CODE_MESSAGES: Record<string, string> = {
  AUTH_REQUIRED: "Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.",
  AUTH_INVALID_TOKEN:
    "Token xác thực không hợp lệ. Vui lòng kiểm tra lại cấu hình.",
  AUTH_ROLE_DENIED:
    "Bạn không có quyền theo vai trò để thực hiện thao tác này.",
  AUTH_SCOPE_DENIED: "Bạn không có quyền nghiệp vụ để thực hiện thao tác này.",
  ITEM_NOT_AVAILABLE: "Truyện không sẵn sàng để xử lý. Vui lòng chọn bản khác.",
  SPLIT_PAYMENT_MISMATCH:
    "Tổng tiền thanh toán chưa khớp với giá trị đơn hàng.",
  ORDER_LOCK_CONFLICT:
    "Dữ liệu đang được xử lý ở phiên khác. Vui lòng thử lại.",
  LOCK_CONFLICT: "Dữ liệu đang được xử lý ở phiên khác. Vui lòng thử lại.",
  CONTRACT_NOT_FOUND: "Không tìm thấy hợp đồng thuê hợp lệ.",
  CONTRACT_NOT_RETURNABLE:
    "Hợp đồng đã đóng hoặc đã hủy, không thể thực hiện kiểm định trả.",
  ITEM_NOT_IN_CONTRACT: "Có truyện không thuộc hợp đồng hiện tại.",
  RETURN_DUPLICATED: "Truyện này đã được ghi nhận trả trước đó.",
  NETWORK_ERROR: "Không thể kết nối backend. Vui lòng kiểm tra dịch vụ cục bộ.",
};

export function toUiErrorMessage(
  code?: string,
  fallbackMessage?: string,
): string {
  if (code && ERROR_CODE_MESSAGES[code]) {
    return ERROR_CODE_MESSAGES[code];
  }

  if (fallbackMessage && fallbackMessage.trim().length > 0) {
    return fallbackMessage;
  }

  return "Đã xảy ra lỗi ngoài dự kiến. Vui lòng thử lại sau.";
}
