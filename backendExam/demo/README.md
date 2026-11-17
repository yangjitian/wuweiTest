# 五维数据后端笔试题

> 本文是五维数据后端笔试题的解答与说明。

基于 Spring Boot 3.2.0 与 Spring Security 的认证示例：先调用登录接口换取会话，再凭会话访问受保护的 `Hello World` 接口，并附带一个静态页面用于演示。

## 题目要求

1. 使用 Spring Boot 3.2.0；
2. 提供一个需要 Spring Security 认证的 `GET` 接口，返回字符串 `Hello World`；
3. 提供用户名密码登录接口，账号 `test` / `123456`；
4. 不引入非必要依赖，并提供静态页面展示效果。

## 关于 JDK 版本

题目要求 JDK 17，但我本机只安装了 JDK 11 和 JDK 21，没有 JDK 17，因此本项目统一使用 **JDK 21** 构建和运行。

- Spring Boot 3.2.0 的最低 Java 版本是 17，JDK 11 无法编译（项目中也用到了 `record` 等 Java 16+ 语法）；
- JDK 21 是 Spring Boot 3.2.0 官方支持的版本，与题目要求的能力一致；
- 如果需要在 JDK 17 环境下运行，把 `pom.xml` 中的 `<java.version>21</java.version>` 改成 `17` 即可，代码无需任何改动。

对应的 IDE 设置：Project SDK 选 21，Maven Runner 的 JRE 也使用 21，`JAVA_HOME` 指向 JDK 21。

## 技术栈

- Java 21、Spring Boot 3.2.0、Spring Security 6.2、Maven
- 只引入 `spring-boot-starter-web` 和 `spring-boot-starter-security`；测试使用 `spring-boot-starter-test` 与 `spring-security-test`
- 没有引入 JWT、Lombok 等额外依赖

## 快速开始

```bash
cd demo
mvn spring-boot:run
```

或者打包后运行：

```bash
mvn clean package
java -jar target/demo-0.0.1-SNAPSHOT.jar
```

启动后访问 <http://localhost:8080/> 打开演示页面。

已在 JDK 21 + Maven 3.9.6 下完成构建与接口验证。

## 接口说明

| 方法 | 路径 | 是否需要认证 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/auth/login` | 否 | 用户名密码登录，成功后建立会话 |
| GET | `/api/hello` | 是 | 返回纯文本 `Hello World` |
| GET | `/api/auth/me` | 是 | 返回当前登录用户 |
| POST | `/api/auth/logout` | 是 | 退出登录并销毁会话 |

演示账号：`test` / `123456`

### 调用示例

```bash
# 1. 登录，保存会话 Cookie
curl -c cookies.txt -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'
# {"code":200,"message":"success","data":{"username":"test","roles":["ROLE_USER"]}}

# 2. 携带会话访问受保护接口
curl -b cookies.txt http://localhost:8080/api/hello
# Hello World

# 3. 未登录访问
curl http://localhost:8080/api/hello
# {"code":401,"message":"未登录或会话已失效","data":null}
```

## 认证实现

- 采用 Cookie + Session：登录时手动调用 `AuthenticationManager` 校验密码，再把 `SecurityContext` 写入 `HttpSession`
- 登录成功后更换 SessionId，防止会话固定攻击
- 未认证访问受保护接口时返回 401 JSON，不重定向到登录页；无权限时返回 403 JSON
- 登录、登出接口免除 CSRF 校验，其余请求保持 Spring Security 的默认防护
- 密码经 BCrypt 加密后存放在内存用户中，不保存明文

## 项目结构

```
demo
├─ src/main/java/com/example/demo
│  ├─ DemoApplication.java
│  ├─ config/SecurityConfig.java         过滤器链、用户与密码编码器
│  ├─ controller/AuthController.java     登录、登出、当前用户
│  ├─ controller/HelloController.java    GET /api/hello
│  ├─ common/ApiResponse.java            统一响应结构
│  ├─ common/GlobalExceptionHandler.java 认证失败与请求体异常的兜底
│  └─ dto/LoginRequestDTO.java、LoginResultDTO.java
└─ src/main/resources
   ├─ application.properties
   └─ static/index.html                  演示页面
```

## 演示页面

页面位于 `src/main/resources/static/index.html`，是一个纯静态页面（HTML + CSS + 原生 JS，无 CDN、无构建工具）：

- 登录后可调用 `/api/hello`，并直接看到状态码、响应体与请求日志
- 提供“不带凭证请求一次”入口，用于观察 401 的返回
- 刷新页面会通过 `/api/auth/me` 恢复登录状态

## 说明

- 演示账号硬编码在 `SecurityConfig` 中，生产环境应从数据库或配置中心读取，密码必须加密存储；
- 当前会话保存在单机内存中，多实例部署需要引入 Spring Session 或改为 Token 方案；
- 页面与接口同源部署，因此没有额外配置 CORS。
