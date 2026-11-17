package com.example.demo.common;

import org.springframework.http.HttpStatus;

/**
 * 统一响应结构，code 与 HTTP 状态码保持一致。
 *
 * @param code    业务状态码
 * @param message 描述信息
 * @param data    响应数据
 * @param <T>     数据类型
 * @author yudi
 */
public record ApiResponse<T>(int code, String message, T data) {

    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(HttpStatus.OK.value(), "success", data);
    }

    public static <T> ApiResponse<T> failure(int code, String message) {
        return new ApiResponse<>(code, message, null);
    }
}
