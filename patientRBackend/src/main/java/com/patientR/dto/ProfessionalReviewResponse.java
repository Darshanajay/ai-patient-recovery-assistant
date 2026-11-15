
package com.patientR.dto;

import java.time.LocalDateTime;

public record ProfessionalReviewResponse(
        Long reviewId,
        Long taskId,
        String taskDescription,
        String decision,
        String comments,
        String professionalName,
        LocalDateTime reviewedAt
) {
}
