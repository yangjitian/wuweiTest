package com.example.demo.dto;

/**
 * 登录请求参数。
 *
 * @param username 用户名
 * @param password 密码
 * @author yudi
 */
public record LoginRequestDTO(String username, String password) {
}
