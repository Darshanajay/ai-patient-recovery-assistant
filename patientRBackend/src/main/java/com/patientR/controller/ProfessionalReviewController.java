
package com.patientR.controller;
import com.patientR.dto.ProfessionalReviewResponse;

import com.patientR.entity.CaregiverTask;
import com.patientR.entity.ProfessionalReview;
import com.patientR.service.ProfessionalReviewService;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/professional-reviews")
@CrossOrigin(origins = "http://localhost:5173")
public class ProfessionalReviewController {

    private final ProfessionalReviewService reviewService;

    public ProfessionalReviewController(
            ProfessionalReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @GetMapping("/pending")
    public List<CaregiverTask> getPendingTasks() {
        return reviewService.getPendingTasks();
    }

    @PostMapping("/{taskId}")
    public ResponseEntity<?> recordReview(
            @PathVariable Long taskId,
            @RequestBody ReviewRequest request,
            Authentication authentication) {

        ProfessionalReview review = reviewService.recordReview(
                taskId,
                authentication.getName(),
                request.decision(),
                request.comments()
        );

        return ResponseEntity.ok(Map.of(
                "message", "Review recorded successfully",
                "reviewId", review.getId(),
                "decision", review.getDecision()
        ));
    }

    @GetMapping("/history/{taskId}")
    public List<ProfessionalReviewResponse> getReviewHistory(
            @PathVariable Long taskId) {
        return reviewService.getSafeTaskHistory(taskId);
    }

    public record ReviewRequest(
            String decision,
            String comments) {
    }
}
