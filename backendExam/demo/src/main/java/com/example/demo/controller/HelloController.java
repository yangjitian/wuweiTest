package com.example.demo.controller;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Hello World 接口，需要认证后才能访问。
 *
 * @author yudi
 */
@RestController
public class HelloController {

    private static final String GREETING = "Hello World";

    @GetMapping(value = "/api/hello", produces = MediaType.TEXT_PLAIN_VALUE)
    public String hello() {
        return GREETING;
    }
}
