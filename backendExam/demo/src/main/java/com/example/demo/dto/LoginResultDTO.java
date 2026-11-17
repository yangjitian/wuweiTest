package com.example.demo.dto;

import java.util.List;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;

/**
 * 登录结果，同时用于返回当前登录用户信息。
 *
 * @param username 用户名
 * @param roles    权限列表
 * @author yudi
 */
public record LoginResultDTO(String username, List<String> roles) {

    public static LoginResultDTO of(Authentication authentication) {
        List<String> roles = authentication.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .toList();
        return new LoginResultDTO(authentication.getName(), roles);
    }
}
