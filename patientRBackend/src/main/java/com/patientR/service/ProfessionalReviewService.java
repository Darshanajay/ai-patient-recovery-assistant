
package com.patientR.service;

import com.patientR.entity.CaregiverTask;
import com.patientR.entity.Professional;
import com.patientR.entity.ProfessionalReview;
import com.patientR.repo.CaregiverTaskRepository;
import com.patientR.repo.ProfessionalRepository;
import com.patientR.repo.ProfessionalReviewRepository;
import com.patientR.dto.ProfessionalReviewResponse;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class ProfessionalReviewService {

    private final ProfessionalReviewRepository reviewRepository;
    private final CaregiverTaskRepository taskRepository;
    private final ProfessionalRepository professionalRepository;

    public ProfessionalReviewService(
            ProfessionalReviewRepository reviewRepository,
            CaregiverTaskRepository taskRepository,
            ProfessionalRepository professionalRepository) {

        this.reviewRepository = reviewRepository;
        this.taskRepository = taskRepository;
        this.professionalRepository = professionalRepository;
    }

    public List<CaregiverTask> getPendingTasks() {
        return taskRepository.findAll()
                .stream()
                .filter(task ->
                        "REQUIRES_REVIEW".equals(
                                task.getVerificationStatus()))
                .toList();
    }

    @Transactional
    public ProfessionalReview recordReview(
            Long taskId,
            String professionalEmail,
            String decision,
            String comments) {

        if (!"REVIEWED".equals(decision)
                && !"NEEDS_CLARIFICATION".equals(decision)) {
            throw new IllegalArgumentException(
                    "Invalid review decision");
        }

        CaregiverTask task = taskRepository.findById(taskId)
                .orElseThrow(() ->
                        new RuntimeException("Task not found"));

        Professional professional = professionalRepository
                .findByEmail(professionalEmail)
                .orElseThrow(() ->
                        new RuntimeException("Professional not found"));

        if (!professional.isActive()
                || !"PROFESSIONAL".equals(professional.getRole())) {
            throw new IllegalArgumentException(
                    "Active professional account required");
        }

        ProfessionalReview review = new ProfessionalReview();
        review.setTask(task);
        review.setProfessional(professional);
        review.setDecision(decision);
        review.setComments(comments);

        return reviewRepository.save(review);
    }

    public List<ProfessionalReview> getTaskHistory(Long taskId) {
        return reviewRepository
                .findByTaskIdOrderByReviewedAtDesc(taskId);
    }
    public List<ProfessionalReviewResponse> getSafeTaskHistory(Long taskId) {

        return reviewRepository
                .findByTaskIdOrderByReviewedAtDesc(taskId)
                .stream()
                .map(review -> new ProfessionalReviewResponse(
                        review.getId(),
                        review.getTask().getId(),
                        review.getTask().getTaskDescription(),
                        review.getDecision(),
                        review.getComments(),
                        review.getProfessional().getFullName(),
                        review.getReviewedAt()
                ))
                .collect(Collectors.toList());
    }
}
