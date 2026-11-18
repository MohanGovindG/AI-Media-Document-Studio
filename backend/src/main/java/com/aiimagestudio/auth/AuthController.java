package com.aiimagestudio.auth;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final Map<String, Map<String, Object>> usersDb = new ConcurrentHashMap<>();

    public AuthController() {
        // Seed default Admin
        Map<String, Object> admin = new HashMap<>();
        admin.put("id", "usr-admin-1");
        admin.put("name", "Mohan Creator");
        admin.put("email", "admin@studio.ai");
        admin.put("password", "password123");
        admin.put("role", "ADMIN");
        admin.put("plan", "Enterprise Unlimited");
        admin.put("avatar", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80");
        admin.put("createdAt", "2026-01-01T00:00:00Z");
        usersDb.put("admin@studio.ai", admin);

        // Seed default Creator
        Map<String, Object> creator = new HashMap<>();
        creator.put("id", "usr-creator-2");
        creator.put("name", "Alex Studio");
        creator.put("email", "creator@studio.ai");
        creator.put("password", "password123");
        creator.put("role", "CREATOR");
        creator.put("plan", "Pro Creator");
        creator.put("avatar", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80");
        creator.put("createdAt", "2026-02-15T00:00:00Z");
        usersDb.put("creator@studio.ai", creator);
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody Map<String, String> data) {
        String name = data.getOrDefault("name", "").trim();
        String email = data.getOrDefault("email", "").trim().toLowerCase();
        String password = data.getOrDefault("password", "");
        String confirmPassword = data.getOrDefault("confirmPassword", "");

        if (name.length() < 2) {
            return ResponseEntity.badRequest().body(Map.of("detail", "Name must be at least 2 characters"));
        }
        if (!email.contains("@") || !email.contains(".")) {
            return ResponseEntity.badRequest().body(Map.of("detail", "Invalid email address format"));
        }
        if (password.length() < 6) {
            return ResponseEntity.badRequest().body(Map.of("detail", "Password must be at least 6 characters"));
        }
        if (!confirmPassword.isEmpty() && !confirmPassword.equals(password)) {
            return ResponseEntity.badRequest().body(Map.of("detail", "Passwords do not match"));
        }

        if (usersDb.containsKey(email)) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of(
                    "detail", "An account with email '" + email + "' already exists. Please login instead."
            ));
        }

        String userId = "usr-" + UUID.randomUUID().toString().substring(0, 8);
        Map<String, Object> newUser = new HashMap<>();
        newUser.put("id", userId);
        newUser.put("name", name);
        newUser.put("email", email);
        newUser.put("password", password);
        newUser.put("role", "USER");
        newUser.put("plan", "Pro Creator Trial");
        newUser.put("createdAt", new Date().toInstant().toString());
        usersDb.put(email, newUser);

        String token = "jwt_token_" + Base64.getUrlEncoder().encodeToString((email + ":" + userId).getBytes());

        Map<String, Object> userPublic = new HashMap<>(newUser);
        userPublic.remove("password");

        return ResponseEntity.ok(Map.of(
                "success", true,
                "message", "User registered successfully",
                "token", token,
                "user", userPublic
        ));
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> credentials) {
        String email = credentials.getOrDefault("email", "").trim().toLowerCase();
        String password = credentials.getOrDefault("password", "");

        if (email.isEmpty() || password.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("detail", "Email and password are required"));
        }

        Map<String, Object> user = usersDb.get(email);
        if (user == null || !password.equals(user.get("password"))) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                    "detail", "Invalid email or password"
            ));
        }

        String token = "jwt_token_" + Base64.getUrlEncoder().encodeToString((email + ":" + user.get("id")).getBytes());

        Map<String, Object> userPublic = new HashMap<>(user);
        userPublic.remove("password");

        return ResponseEntity.ok(Map.of(
                "success", true,
                "message", "Login successful",
                "token", token,
                "user", userPublic
        ));
    }

    @GetMapping("/me")
    public ResponseEntity<?> getCurrentUser(@RequestHeader(value = "Authorization", required = false) String authHeader) {
        String email = "admin@studio.ai";
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            if (token.startsWith("jwt_token_")) {
                try {
                    String decoded = new String(Base64.getUrlDecoder().decode(token.substring(10)));
                    email = decoded.split(":")[0];
                } catch (Exception ignored) {}
            }
        }

        Map<String, Object> user = usersDb.getOrDefault(email, usersDb.get("admin@studio.ai"));
        Map<String, Object> userPublic = new HashMap<>(user);
        userPublic.remove("password");

        return ResponseEntity.ok(Map.of(
                "success", true,
                "user", userPublic
        ));
    }

    @PutMapping("/profile")
    public ResponseEntity<?> updateProfile(
            @RequestHeader(value = "Authorization", required = false) String authHeader,
            @RequestBody Map<String, String> data
    ) {
        String email = "admin@studio.ai";
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            if (token.startsWith("jwt_token_")) {
                try {
                    String decoded = new String(Base64.getUrlDecoder().decode(token.substring(10)));
                    email = decoded.split(":")[0];
                } catch (Exception ignored) {}
            }
        }

        Map<String, Object> user = usersDb.get(email);
        if (user == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("detail", "User not found"));
        }

        if (data.containsKey("name") && data.get("name").trim().length() >= 2) {
            user.put("name", data.get("name").trim());
        }

        Map<String, Object> userPublic = new HashMap<>(user);
        userPublic.remove("password");

        return ResponseEntity.ok(Map.of(
                "success", true,
                "message", "Profile updated successfully",
                "user", userPublic
        ));
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout() {
        return ResponseEntity.ok(Map.of("success", true, "message", "Logged out successfully"));
    }
}
