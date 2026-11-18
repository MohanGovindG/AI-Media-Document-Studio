package com.aiimagestudio.conversion;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

@RestController
@RequestMapping("/api/backend/images")
public class ConversionController {

    private final RestTemplate restTemplate;

    @Value("${ai.service.url:http://127.0.0.1:8000}")
    private String aiServiceUrl;

    public ConversionController(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @GetMapping("/formats")
    public ResponseEntity<?> getFormats() {
        return restTemplate.getForEntity(aiServiceUrl + "/api/images/formats", Object.class);
    }

    @GetMapping("/formats/{format}")
    public ResponseEntity<?> getFormatTargets(@PathVariable String format) {
        return restTemplate.getForEntity(aiServiceUrl + "/api/images/formats/" + format, Object.class);
    }
}
