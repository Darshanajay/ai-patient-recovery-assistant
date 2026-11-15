
package com.patientR.controller;

import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @GetMapping("/me")
    public Map<String, Object> getCurrentProfessional(
            Authentication authentication) {

        return Map.of(
                "authenticated", authentication.isAuthenticated(),
                "email", authentication.getName(),
                "roles", authentication.getAuthorities()
        );
    }
}
